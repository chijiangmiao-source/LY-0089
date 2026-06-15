import random
from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db import transaction
from ninja import Router, Query
from ninja.errors import HttpError
from ninja.pagination import paginate

from carts.models import Cart
from stations.models import ServiceStation
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
    )


def generate_rental_no() -> str:
    now = datetime.now()
    time_part = now.strftime('%Y%m%d%H%M%S')
    random_part = ''.join(random.choices('0123456789', k=4))
    return f'RL{time_part}{random_part}'


@router.get('/', response=list[RentalOut])
@paginate
def list_rentals(request, stage: str = None, user_phone: str = None):
    queryset = RentalRecord.objects.select_related('borrow_station', 'return_station', 'cart').all()
    if stage:
        queryset = queryset.filter(stage=stage)
    if user_phone:
        queryset = queryset.filter(user_phone=user_phone)
    return [rental_to_out(record) for record in queryset]


@router.get('/{rental_id}', response=RentalOut)
def get_rental(request, rental_id: int):
    record = get_object_or_404(
        RentalRecord.objects.select_related('borrow_station', 'return_station', 'cart'),
        id=rental_id
    )
    return rental_to_out(record)


@router.post('/borrow', response=RentalOut)
@transaction.atomic
def borrow_cart(request, payload: BorrowIn):
    cart = get_object_or_404(Cart, id=payload.cart_id)
    if cart.status != 'available':
        raise HttpError(400, '该推车不可借出')

    overdue_exists = RentalRecord.objects.filter(
        user_phone=payload.user_phone,
        stage='overdue'
    ).exists()
    if overdue_exists:
        raise HttpError(400, '该手机号存在逾期未还记录，不能借车')

    borrow_station = get_object_or_404(ServiceStation, id=payload.borrow_station_id)

    rental_no = generate_rental_no()
    now = datetime.now()

    record = RentalRecord.objects.create(
        rental_no=rental_no,
        user_phone=payload.user_phone,
        borrow_time=now,
        borrow_station=borrow_station,
        cart=cart,
        stage='borrowing',
    )

    cart.status = 'borrowed'
    cart.save()

    record.refresh_from_db()
    record = RentalRecord.objects.select_related('borrow_station', 'return_station', 'cart').get(id=record.id)
    return rental_to_out(record)


@router.post('/return', response=RentalOut)
@transaction.atomic
def return_cart(request, payload: ReturnIn):
    record = get_object_or_404(RentalRecord, rental_no=payload.rental_no)
    if record.stage not in ('borrowing', 'overdue'):
        raise HttpError(400, '该记录状态不允许归还')

    cart = record.cart
    if cart.status != 'borrowed':
        raise HttpError(400, '推车状态异常，无法归还')

    return_station = get_object_or_404(ServiceStation, id=payload.return_station_id)

    now = datetime.now()
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
        record.stage = 'overdue'

    record.save()
    cart.save()

    record.refresh_from_db()
    record = RentalRecord.objects.select_related('borrow_station', 'return_station', 'cart').get(id=record.id)
    return rental_to_out(record)


@router.get('/check-phone/{phone}')
def check_phone(request, phone: str):
    overdue_exists = RentalRecord.objects.filter(
        user_phone=phone,
        stage='overdue'
    ).exists()
    if overdue_exists:
        return {
            'can_borrow': False,
            'reason': '该手机号存在逾期未还记录，不能借车'
        }
    return {
        'can_borrow': True,
        'reason': ''
    }
