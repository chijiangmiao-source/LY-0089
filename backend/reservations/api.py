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
from rentals.models import RentalRecord
from .models import CartReservation
from .schemas import ReservationCreateIn, ReservationOut, ReservationPickupIn
from .utils import cleanup_expired_reservations


router = Router()


def generate_reservation_no() -> str:
    now = timezone.now()
    time_part = now.strftime('%Y%m%d%H%M%S')
    random_part = ''.join(random.choices('0123456789', k=4))
    return f'RS{time_part}{random_part}'


def reservation_to_out(reservation: CartReservation) -> ReservationOut:
    return ReservationOut(
        id=reservation.id,
        reservation_no=reservation.reservation_no,
        user_phone=reservation.user_phone,
        station_id=reservation.station_id,
        station_name=reservation.station.name if reservation.station else '',
        cart_id=reservation.cart_id,
        cart_no=reservation.cart.cart_no if reservation.cart else None,
        reserve_time=reservation.reserve_time,
        expire_time=reservation.expire_time,
        pickup_time=reservation.pickup_time,
        status=reservation.status,
        status_display=reservation.status_display,
        is_expired=reservation.is_expired,
    )


@router.get('/', response=list[ReservationOut])
@paginate
def list_reservations(request, status: str = None, user_phone: str = None, station_id: int = None):
    cleanup_expired_reservations()
    queryset = CartReservation.objects.select_related('station', 'cart').all()
    if status:
        queryset = queryset.filter(status=status)
    if user_phone:
        queryset = queryset.filter(user_phone=user_phone)
    if station_id:
        queryset = queryset.filter(station_id=station_id)
    return [reservation_to_out(r) for r in queryset]


@router.get('/{reservation_id}', response=ReservationOut)
def get_reservation(request, reservation_id: int):
    cleanup_expired_reservations()
    reservation = get_object_or_404(
        CartReservation.objects.select_related('station', 'cart'),
        id=reservation_id
    )
    return reservation_to_out(reservation)


@router.post('/', response=ReservationOut)
@transaction.atomic
def create_reservation(request, payload: ReservationCreateIn):
    cleanup_expired_reservations()
    station = get_object_or_404(ServiceStation, id=payload.station_id)

    existing_active = CartReservation.objects.filter(
        user_phone=payload.user_phone,
        status='active'
    ).first()
    if existing_active:
        raise HttpError(400, '该手机号已有进行中的预约')

    cart_filters = {
        'station_id': payload.station_id,
        'status': 'available',
    }
    if payload.cart_type:
        cart_filters['cart_type'] = payload.cart_type

    available_cart = Cart.objects.filter(**cart_filters).first()
    if not available_cart:
        raise HttpError(400, '该服务点暂无可用推车')

    if available_cart.status == 'maintenance':
        raise HttpError(400, '该推车正在维修中，不可预约')
    if available_cart.status == 'scrapped':
        raise HttpError(400, '该推车已报废，不可预约')

    now = timezone.now()
    expire_minutes = getattr(settings, 'RESERVATION_EXPIRE_MINUTES', 15)
    expire_time = now + timedelta(minutes=expire_minutes)

    reservation_no = generate_reservation_no()

    reservation = CartReservation.objects.create(
        reservation_no=reservation_no,
        user_phone=payload.user_phone,
        station=station,
        cart=available_cart,
        reserve_time=now,
        expire_time=expire_time,
        status='active',
    )

    available_cart.status = 'reserved'
    available_cart.save()

    reservation.refresh_from_db()
    reservation = CartReservation.objects.select_related('station', 'cart').get(id=reservation.id)
    return reservation_to_out(reservation)


@router.put('/{reservation_id}/cancel', response=ReservationOut)
@transaction.atomic
def cancel_reservation(request, reservation_id: int):
    cleanup_expired_reservations()
    reservation = get_object_or_404(
        CartReservation.objects.select_related('station', 'cart'),
        id=reservation_id
    )
    if reservation.status != 'active':
        raise HttpError(400, '只有预约中的记录可以取消')

    reservation.status = 'cancelled'
    reservation.save()

    if reservation.cart and reservation.cart.status == 'reserved':
        reservation.cart.status = 'available'
        reservation.cart.save()

    return reservation_to_out(reservation)


@router.post('/expire-expired')
@transaction.atomic
def expire_expired_reservations(request):
    now = timezone.now()
    expired_reservations = CartReservation.objects.filter(
        status='active',
        expire_time__lt=now
    ).select_related('cart')

    count = 0
    for reservation in expired_reservations:
        reservation.status = 'expired'
        reservation.save()

        if reservation.cart and reservation.cart.status == 'reserved':
            reservation.cart.status = 'available'
            reservation.cart.save()
        count += 1

    return {'expired_count': count}


@router.post('/pickup', response=dict)
@transaction.atomic
def pickup_reserved_cart(request, payload: ReservationPickupIn):
    cleanup_expired_reservations()
    from rentals.api import generate_rental_no, rental_to_out

    reservation = get_object_or_404(
        CartReservation.objects.select_related('station', 'cart'),
        reservation_no=payload.reservation_no
    )

    if reservation.status != 'active':
        raise HttpError(400, '该预约已失效或已完成')

    if reservation.is_expired:
        reservation.status = 'expired'
        reservation.save()
        if reservation.cart and reservation.cart.status == 'reserved':
            reservation.cart.status = 'available'
            reservation.cart.save()
        raise HttpError(400, '预约已超时失效')

    if reservation.user_phone != payload.borrow_station_id:
        pass

    overdue_unreturned = RentalRecord.objects.filter(
        user_phone=reservation.user_phone,
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

    cart = get_object_or_404(Cart, id=payload.cart_id)
    if cart.status != 'reserved':
        raise HttpError(400, '该推车未被预约')

    if reservation.cart_id and reservation.cart_id != cart.id:
        raise HttpError(400, '预约推车与取车推车不匹配')

    borrow_station = get_object_or_404(ServiceStation, id=payload.borrow_station_id)

    rental_no = generate_rental_no()
    now = timezone.now()

    rental_record = RentalRecord.objects.create(
        rental_no=rental_no,
        user_phone=reservation.user_phone,
        borrow_time=now,
        borrow_station=borrow_station,
        cart=cart,
        stage='borrowing',
        is_overdue=False,
    )

    cart.status = 'borrowed'
    cart.save()

    reservation.status = 'completed'
    reservation.pickup_time = now
    reservation.save()

    rental_record.refresh_from_db()
    rental_record = RentalRecord.objects.select_related('borrow_station', 'return_station', 'cart').get(id=rental_record.id)

    return {
        'reservation': reservation_to_out(reservation),
        'rental': rental_to_out(rental_record),
    }


@router.get('/check-active/{phone}')
def check_active_reservation(request, phone: str):
    cleanup_expired_reservations()
    active_reservation = CartReservation.objects.filter(
        user_phone=phone,
        status='active'
    ).select_related('station', 'cart').first()

    if active_reservation:
        if active_reservation.is_expired:
            return {
                'has_active': False,
                'reason': '预约已超时失效'
            }
        return {
            'has_active': True,
            'reservation': reservation_to_out(active_reservation),
            'reason': ''
        }
    return {
        'has_active': False,
        'reason': ''
    }
