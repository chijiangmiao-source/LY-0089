from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count, Sum, Q
from django.utils import timezone
from ninja import Router
from pydantic import BaseModel
from typing import List, Optional

from carts.models import Cart
from stations.models import ServiceStation
from stranded.models import StrandedRecord
from transfers.models import TransferOrder
from rentals.models import RentalRecord
from reservations.models import CartReservation
from reservations.utils import cleanup_expired_reservations

router = Router()


class OverviewOut(BaseModel):
    total_carts: int
    available_carts: int
    reserved_carts: int
    borrowed_carts: int
    stranded_carts: int
    transferring_carts: int
    total_stations: int
    active_reservations: int


class StationShortageOut(BaseModel):
    id: int
    name: str
    safety_stock: int
    current_count: int
    shortage_count: int


class FloorShortageOut(BaseModel):
    floor: int
    total_carts: int
    available_carts: int
    shortage: int
    stations: List[StationShortageOut]


class StrandedDistributionOut(BaseModel):
    less_than_1h: int
    one_to_4h: int
    four_to_12h: int
    more_than_12h: int


class TransferRateOut(BaseModel):
    total_transfers: int
    completed_transfers: int
    pending_transfers: int
    in_progress_transfers: int
    completion_rate: float


class OverdueRentalOut(BaseModel):
    id: int
    rental_no: str
    user_phone: str
    borrow_time: datetime
    borrow_station_id: int
    borrow_station_name: str
    cart_id: int
    cart_no: str
    stage: str
    stage_display: str
    overdue_hours: float


class ReservationOut(BaseModel):
    id: int
    reservation_no: str
    user_phone: str
    station_id: int
    station_name: str
    cart_id: Optional[int] = None
    cart_no: Optional[str] = None
    reserve_time: datetime
    expire_time: datetime
    minutes_left: float


class FloorReservationHeatOut(BaseModel):
    floor: int
    total_reservations: int
    active_reservations: int
    stations: List[dict]


@router.get('/overview', response=OverviewOut)
def get_overview(request):
    cleanup_expired_reservations()
    total_carts = Cart.objects.count()
    available_carts = Cart.objects.filter(status='available').count()
    reserved_carts = Cart.objects.filter(status='reserved').count()
    borrowed_carts = Cart.objects.filter(status='borrowed').count()
    stranded_carts = Cart.objects.filter(status='stranded').count()
    transferring_carts = Cart.objects.filter(status='transferring').count()
    total_stations = ServiceStation.objects.filter(is_active=True).count()
    active_reservations = CartReservation.objects.filter(status='active').count()

    return OverviewOut(
        total_carts=total_carts,
        available_carts=available_carts,
        reserved_carts=reserved_carts,
        borrowed_carts=borrowed_carts,
        stranded_carts=stranded_carts,
        transferring_carts=transferring_carts,
        total_stations=total_stations,
        active_reservations=active_reservations,
    )


@router.get('/floor-shortage', response=List[FloorShortageOut])
def get_floor_shortage(request):
    cleanup_expired_reservations()
    stations = ServiceStation.objects.filter(is_active=True).order_by('floor')
    floor_data = {}

    for station in stations:
        current_count = Cart.objects.filter(station_id=station.id, status='available').count()
        shortage_count = max(0, station.safety_stock - current_count)

        if station.floor not in floor_data:
            floor_data[station.floor] = {
                'floor': station.floor,
                'total_carts': 0,
                'available_carts': 0,
                'safety_stock_sum': 0,
                'stations': [],
            }

        station_carts_total = Cart.objects.filter(station_id=station.id).count()
        floor_data[station.floor]['total_carts'] += station_carts_total
        floor_data[station.floor]['available_carts'] += current_count
        floor_data[station.floor]['safety_stock_sum'] += station.safety_stock
        floor_data[station.floor]['stations'].append(StationShortageOut(
            id=station.id,
            name=station.name,
            safety_stock=station.safety_stock,
            current_count=current_count,
            shortage_count=shortage_count,
        ))

    result = []
    for floor in sorted(floor_data.keys()):
        data = floor_data[floor]
        shortage = max(0, data['safety_stock_sum'] - data['available_carts'])
        result.append(FloorShortageOut(
            floor=data['floor'],
            total_carts=data['total_carts'],
            available_carts=data['available_carts'],
            shortage=shortage,
            stations=data['stations'],
        ))

    return result


@router.get('/stranded-distribution', response=StrandedDistributionOut)
def get_stranded_distribution(request):
    cleanup_expired_reservations()
    now = timezone.now()
    records = StrandedRecord.objects.all()

    less_than_1h = 0
    one_to_4h = 0
    four_to_12h = 0
    more_than_12h = 0

    for record in records:
        if record.recycled_at:
            duration = (record.recycled_at - record.reported_at).total_seconds() / 3600
        else:
            duration = (now - record.reported_at).total_seconds() / 3600

        if duration < 1:
            less_than_1h += 1
        elif duration < 4:
            one_to_4h += 1
        elif duration < 12:
            four_to_12h += 1
        else:
            more_than_12h += 1

    return StrandedDistributionOut(
        less_than_1h=less_than_1h,
        one_to_4h=one_to_4h,
        four_to_12h=four_to_12h,
        more_than_12h=more_than_12h,
    )


@router.get('/transfer-rate', response=TransferRateOut)
def get_transfer_rate(request):
    cleanup_expired_reservations()
    total_transfers = TransferOrder.objects.count()
    completed_transfers = TransferOrder.objects.filter(status='completed').count()
    pending_transfers = TransferOrder.objects.filter(status='pending').count()
    in_progress_transfers = TransferOrder.objects.filter(status='transiting').count()

    if total_transfers > 0:
        completion_rate = round(completed_transfers / total_transfers * 100, 2)
    else:
        completion_rate = 0.0

    return TransferRateOut(
        total_transfers=total_transfers,
        completed_transfers=completed_transfers,
        pending_transfers=pending_transfers,
        in_progress_transfers=in_progress_transfers,
        completion_rate=completion_rate,
    )


@router.get('/overdue-list', response=List[OverdueRentalOut])
def get_overdue_list(request):
    cleanup_expired_reservations()
    now = timezone.now()
    overdue_hours_threshold = settings.RENTAL_OVERDUE_HOURS
    threshold_time = now - timedelta(hours=overdue_hours_threshold)

    queryset = RentalRecord.objects.select_related('borrow_station', 'cart').filter(
        Q(stage='overdue') | Q(stage='borrowing', borrow_time__lt=threshold_time)
    ).order_by('-borrow_time')

    result = []
    for record in queryset:
        duration_hours = (now - record.borrow_time).total_seconds() / 3600
        result.append(OverdueRentalOut(
            id=record.id,
            rental_no=record.rental_no,
            user_phone=record.user_phone,
            borrow_time=record.borrow_time,
            borrow_station_id=record.borrow_station_id,
            borrow_station_name=record.borrow_station.name if record.borrow_station else '',
            cart_id=record.cart_id,
            cart_no=record.cart.cart_no if record.cart else '',
            stage=record.stage,
            stage_display=record.stage_display,
            overdue_hours=round(duration_hours, 2),
        ))

    return result


@router.get('/upcoming-expiring-reservations', response=List[ReservationOut])
def get_upcoming_expiring_reservations(request, minutes: int = 5):
    cleanup_expired_reservations()
    now = timezone.now()
    threshold_time = now + timedelta(minutes=minutes)

    queryset = CartReservation.objects.select_related('station', 'cart').filter(
        status='active',
        expire_time__gt=now,
        expire_time__lte=threshold_time
    ).order_by('expire_time')

    result = []
    for reservation in queryset:
        minutes_left = (reservation.expire_time - now).total_seconds() / 60
        result.append(ReservationOut(
            id=reservation.id,
            reservation_no=reservation.reservation_no,
            user_phone=reservation.user_phone,
            station_id=reservation.station_id,
            station_name=reservation.station.name if reservation.station else '',
            cart_id=reservation.cart_id,
            cart_no=reservation.cart.cart_no if reservation.cart else None,
            reserve_time=reservation.reserve_time,
            expire_time=reservation.expire_time,
            minutes_left=round(minutes_left, 2),
        ))

    return result


@router.get('/floor-reservation-heat', response=List[FloorReservationHeatOut])
def get_floor_reservation_heat(request, hours: int = 24):
    cleanup_expired_reservations()
    now = timezone.now()
    start_time = now - timedelta(hours=hours)

    stations = ServiceStation.objects.filter(is_active=True).order_by('floor')
    floor_data = {}

    for station in stations:
        total_reservations = CartReservation.objects.filter(
            station_id=station.id,
            created_at__gte=start_time
        ).count()
        active_reservations = CartReservation.objects.filter(
            station_id=station.id,
            status='active'
        ).count()

        if station.floor not in floor_data:
            floor_data[station.floor] = {
                'floor': station.floor,
                'total_reservations': 0,
                'active_reservations': 0,
                'stations': [],
            }

        floor_data[station.floor]['total_reservations'] += total_reservations
        floor_data[station.floor]['active_reservations'] += active_reservations
        floor_data[station.floor]['stations'].append({
            'station_id': station.id,
            'station_name': station.name,
            'total_reservations': total_reservations,
            'active_reservations': active_reservations,
        })

    result = []
    for floor in sorted(floor_data.keys()):
        data = floor_data[floor]
        data['stations'].sort(key=lambda x: x['total_reservations'], reverse=True)
        result.append(FloorReservationHeatOut(**data))

    result.sort(key=lambda x: x.total_reservations, reverse=True)
    return result
