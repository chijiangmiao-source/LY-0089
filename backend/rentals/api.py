import random
from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from ninja import Router, Query
from ninja.errors import HttpError
from ninja.pagination import paginate

from carts.models import Cart
from stations.models import ServiceStation
from reservations.models import CartReservation
from reservations.utils import cleanup_expired_reservations
from .models import RentalRecord
from .schemas import BorrowIn, ReturnIn, RentalOut


router = Router()


def rental_to_out(record: RentalRecord) -> RentalOut:
    return RentalOut(
        id=record.id,
        rental_no=record.rental_no,
        user_phone=record.user_phone,
        borrow_time=record.borrow_time,
        return_time=record.return_time,
        borrow_station_id=record.borrow_station_id,
        borrow_station_name=record.borrow_station.name if record.borrow_station else '',
        return_station_id=record.return_station_id,
        return_station_name=record.return_station.name if record.return_station else None,
        cart_id=record.cart_id,
        cart_no=record.cart.cart_no if record.cart else '',
        stage=record.stage,
        stage_display=record.stage_display,
        is_overdue=record.is_overdue or False,
    )


def generate_rental_no() -> str:
    now = timezone.now()
    time_part = now.strftime('%Y%m%d%H%M%S')
    random_part = ''.join(random.choices('0123456789', k=4))
    return f'RL{time_part}{random_part}'


@router.get('/', response=list[RentalOut])
@paginate
def list_rentals(request, stage: str = None, user_phone: str = None):
    cleanup_expired_reservations()
    queryset = RentalRecord.objects.select_related('borrow_station', 'return_station', 'cart').all()
    if stage:
        queryset = queryset.filter(stage=stage)
    if user_phone:
        queryset = queryset.filter(user_phone=user_phone)
    return [rental_to_out(record) for record in queryset]


@router.get('/{rental_id}', response=RentalOut)
def get_rental(request, rental_id: int):
    cleanup_expired_reservations()
    record = get_object_or_404(
        RentalRecord.objects.select_related('borrow_station', 'return_station', 'cart'),
        id=rental_id
    )
    return rental_to_out(record)


@router.post('/borrow', response=RentalOut)
@transaction.atomic
def borrow_cart(request, payload: BorrowIn):
    cleanup_expired_reservations()
    cart = get_object_or_404(Cart, id=payload.cart_id)
    if cart.status == 'maintenance':
        raise HttpError(400, '该推车正在维修中，不可借出')
    if cart.status == 'scrapped':
        raise HttpError(400, '该推车已报废，不可借出')
    if cart.status not in ['available', 'reserved']:
        raise HttpError(400, '该推车不可借出')

    if cart.status == 'reserved':
        active_reservation = CartReservation.objects.filter(
            cart_id=cart.id,
            status='active',
            user_phone=payload.user_phone
        ).first()
        if not active_reservation:
            raise HttpError(400, '该推车已被其他用户预约，请先取消预约或选择其他推车')
        if active_reservation.is_expired:
            active_reservation.status = 'expired'
            active_reservation.save()
            if cart.status == 'reserved':
                cart.status = 'available'
                cart.save()
            raise HttpError(400, '该推车预约已超时失效，请重新预约')

        active_reservation.status = 'completed'
        active_reservation.pickup_time = timezone.now()
        active_reservation.save()

    active_reservation_check = CartReservation.objects.filter(
        user_phone=payload.user_phone,
        status='active'
    ).exclude(cart_id=cart.id).first()
    if active_reservation_check and active_reservation_check.cart_id != cart.id:
        raise HttpError(400, '该手机号已有进行中的预约，请先使用或取消预约')

    overdue_unreturned = RentalRecord.objects.filter(
        user_phone=payload.user_phone,
        stage__in=['borrowing', 'overdue']
    )
    overdue_hours_threshold = settings.RENTAL_OVERDUE_HOURS
    now_check = timezone.now()
    can_borrow = True
    for rec in overdue_unreturned:
        duration = (now_check - rec.borrow_time).total_seconds() / 3600
        if duration > overdue_hours_threshold or rec.stage == 'overdue':
            can_borrow = False
            break
    if not can_borrow:
        raise HttpError(400, '该手机号存在逾期未还记录，不能借车')

    borrow_station = get_object_or_404(ServiceStation, id=payload.borrow_station_id)

    rental_no = generate_rental_no()
    now = timezone.now()

    record = RentalRecord.objects.create(
        rental_no=rental_no,
        user_phone=payload.user_phone,
        borrow_time=now,
        borrow_station=borrow_station,
        cart=cart,
        stage='borrowing',
        is_overdue=False,
    )

    cart.status = 'borrowed'
    cart.save()

    record.refresh_from_db()
    record = RentalRecord.objects.select_related('borrow_station', 'return_station', 'cart').get(id=record.id)
    return rental_to_out(record)


@router.post('/return', response=RentalOut)
@transaction.atomic
def return_cart(request, payload: ReturnIn):
    cleanup_expired_reservations()
    record = get_object_or_404(RentalRecord, rental_no=payload.rental_no)
    if record.stage not in ('borrowing', 'overdue'):
        raise HttpError(400, '该记录状态不允许归还')

    cart = record.cart
    if cart.status != 'borrowed':
        raise HttpError(400, '推车状态异常，无法归还')

    return_station = get_object_or_404(ServiceStation, id=payload.return_station_id)

    now = timezone.now()
    record.return_time = now
    record.return_station = return_station
    record.stage = 'returned'

    if return_station.id != record.borrow_station_id:
        cart.status = 'reset_check'
    else:
        cart.status = 'available'

    overdue_hours = settings.RENTAL_OVERDUE_HOURS
    borrow_duration = now - record.borrow_time
    if borrow_duration > timedelta(hours=overdue_hours):
        record.is_overdue = True

    record.save()
    cart.save()

    record.refresh_from_db()
    record = RentalRecord.objects.select_related('borrow_station', 'return_station', 'cart').get(id=record.id)
    return rental_to_out(record)


@router.get('/check-phone/{phone}')
def check_phone(request, phone: str):
    cleanup_expired_reservations()
    overdue_hours_threshold = settings.RENTAL_OVERDUE_HOURS
    now = timezone.now()
    unreturned_records = RentalRecord.objects.filter(
        user_phone=phone,
        stage__in=['borrowing', 'overdue']
    )
    for rec in unreturned_records:
        duration = (now - rec.borrow_time).total_seconds() / 3600
        if duration > overdue_hours_threshold or rec.stage == 'overdue':
            return {
                'can_borrow': False,
                'reason': '该手机号存在逾期未还记录，不能借车'
            }

    active_reservation = CartReservation.objects.filter(
        user_phone=phone,
        status='active'
    ).first()
    if active_reservation:
        if active_reservation.is_expired:
            return {
                'can_borrow': True,
                'has_reservation': True,
                'reservation_expired': True,
                'reason': '存在已超时的预约，已自动失效'
            }
        return {
            'can_borrow': True,
            'has_reservation': True,
            'reservation_expired': False,
            'reservation_no': active_reservation.reservation_no,
            'cart_id': active_reservation.cart_id,
            'expire_time': active_reservation.expire_time,
            'reason': '存在进行中的预约'
        }

    return {
        'can_borrow': True,
        'has_reservation': False,
        'reason': ''
    }
