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
from maintenance.models import MaintenanceRecord
from reservations.utils import cleanup_expired_reservations
from venues.models import Venue
from cross_venue_transfers.models import CrossVenueTransfer

router = Router()


class OverviewOut(BaseModel):
    total_carts: int
    available_carts: int
    reserved_carts: int
    borrowed_carts: int
    stranded_carts: int
    transferring_carts: int
    maintenance_carts: int
    scrapped_carts: int
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


class FloorFaultOut(BaseModel):
    floor: int
    total_faults: int
    pending_count: int
    repairing_count: int
    stations: List[dict]


@router.get('/overview', response=OverviewOut)
def get_overview(request):
    cleanup_expired_reservations()
    total_carts = Cart.objects.exclude(status='scrapped').count()
    available_carts = Cart.objects.filter(status='available').count()
    reserved_carts = Cart.objects.filter(status='reserved').count()
    borrowed_carts = Cart.objects.filter(status='borrowed').count()
    stranded_carts = Cart.objects.filter(status='stranded').count()
    transferring_carts = Cart.objects.filter(status='transferring').count()
    maintenance_carts = Cart.objects.filter(status='maintenance').count()
    scrapped_carts = Cart.objects.filter(status='scrapped').count()
    total_stations = ServiceStation.objects.filter(is_active=True).count()
    active_reservations = CartReservation.objects.filter(status='active').count()

    return OverviewOut(
        total_carts=total_carts,
        available_carts=available_carts,
        reserved_carts=reserved_carts,
        borrowed_carts=borrowed_carts,
        stranded_carts=stranded_carts,
        transferring_carts=transferring_carts,
        maintenance_carts=maintenance_carts,
        scrapped_carts=scrapped_carts,
        total_stations=total_stations,
        active_reservations=active_reservations,
    )


@router.get('/floor-shortage', response=List[FloorShortageOut])
def get_floor_shortage(request):
    cleanup_expired_reservations()
    stations = ServiceStation.objects.filter(is_active=True).order_by('floor')
    floor_data = {}

    for station in stations:
        current_count = Cart.objects.filter(
            station_id=station.id, status='available'
        ).exclude(status__in=['maintenance', 'scrapped']).count()
        shortage_count = max(0, station.safety_stock - current_count)

        if station.floor not in floor_data:
            floor_data[station.floor] = {
                'floor': station.floor,
                'total_carts': 0,
                'available_carts': 0,
                'safety_stock_sum': 0,
                'stations': [],
            }

        station_carts_total = Cart.objects.filter(
            station_id=station.id
        ).exclude(status='scrapped').count()
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


@router.get('/floor-fault-distribution', response=List[FloorFaultOut])
def get_floor_fault_distribution(request):
    cleanup_expired_reservations()
    stations = ServiceStation.objects.filter(is_active=True).order_by('floor')
    floor_data = {}

    for station in stations:
        pending_records = MaintenanceRecord.objects.filter(
            report_station_id=station.id,
            status='pending'
        ).count()
        repairing_records = MaintenanceRecord.objects.filter(
            report_station_id=station.id,
            status='repairing'
        ).count()
        station_total = pending_records + repairing_records

        if station.floor not in floor_data:
            floor_data[station.floor] = {
                'floor': station.floor,
                'total_faults': 0,
                'pending_count': 0,
                'repairing_count': 0,
                'stations': [],
            }

        floor_data[station.floor]['total_faults'] += station_total
        floor_data[station.floor]['pending_count'] += pending_records
        floor_data[station.floor]['repairing_count'] += repairing_records
        floor_data[station.floor]['stations'].append({
            'station_id': station.id,
            'station_name': station.name,
            'total_faults': station_total,
            'pending_count': pending_records,
            'repairing_count': repairing_records,
        })

    result = []
    for floor in sorted(floor_data.keys()):
        data = floor_data[floor]
        data['stations'].sort(key=lambda x: x['total_faults'], reverse=True)
        result.append(FloorFaultOut(**data))

    result.sort(key=lambda x: x.total_faults, reverse=True)
    return result


class VenueOverviewOut(BaseModel):
    venue_id: int
    venue_name: str
    venue_type: str
    venue_type_display: str
    total_carts: int
    available_carts: int
    borrowed_carts: int
    reserved_carts: int
    stranded_carts: int
    maintenance_carts: int
    total_stations: int
    active_reservations: int
    today_borrow_count: int
    today_return_count: int
    pending_maintenance: int
    shortage_count: int


class CrossVenueShortageOut(BaseModel):
    venue_id: int
    venue_name: str
    total_safety_stock: int
    current_available: int
    shortage: int
    urgent_need: int
    affected_stations: List[dict]


class CrossVenueTransferRateOut(BaseModel):
    total_cross_transfers: int
    pending_approval: int
    approved: int
    rejected: int
    in_transit: int
    arrived: int
    confirmed: int
    completion_rate: float
    urgent_count: int
    avg_transport_hours: float
    by_venue: List[dict]


@router.get('/venue-overview', response=List[VenueOverviewOut])
def get_venue_overview(request):
    cleanup_expired_reservations()
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    venues = Venue.objects.filter(is_active=True)
    result = []

    for venue in venues:
        stations = ServiceStation.objects.filter(venue_id=venue.id, is_active=True)
        station_ids = list(stations.values_list('id', flat=True))

        carts_qs = Cart.objects.filter(station_id__in=station_ids).exclude(status='scrapped')
        total_carts = carts_qs.count()
        available_carts = carts_qs.filter(status='available').count()
        borrowed_carts = carts_qs.filter(status='borrowed').count()
        reserved_carts = carts_qs.filter(status='reserved').count()
        stranded_carts = carts_qs.filter(status='stranded').count()
        maintenance_carts = carts_qs.filter(status='maintenance').count()

        total_stations = stations.count()
        active_reservations = CartReservation.objects.filter(
            station_id__in=station_ids, status='active'
        ).count()

        today_borrow_count = RentalRecord.objects.filter(
            borrow_station_id__in=station_ids,
            borrow_time__gte=today_start
        ).count()

        today_return_count = RentalRecord.objects.filter(
            return_station_id__in=station_ids,
            return_time__gte=today_start
        ).count()

        pending_maintenance = MaintenanceRecord.objects.filter(
            report_station_id__in=station_ids,
            status__in=['pending', 'repairing']
        ).count()

        total_safety_stock = sum(s.safety_stock for s in stations)
        shortage_count = max(0, total_safety_stock - available_carts)

        result.append(VenueOverviewOut(
            venue_id=venue.id,
            venue_name=venue.name,
            venue_type=venue.venue_type,
            venue_type_display=venue.venue_type_display,
            total_carts=total_carts,
            available_carts=available_carts,
            borrowed_carts=borrowed_carts,
            reserved_carts=reserved_carts,
            stranded_carts=stranded_carts,
            maintenance_carts=maintenance_carts,
            total_stations=total_stations,
            active_reservations=active_reservations,
            today_borrow_count=today_borrow_count,
            today_return_count=today_return_count,
            pending_maintenance=pending_maintenance,
            shortage_count=shortage_count,
        ))

    return result


@router.get('/cross-venue-shortage', response=List[CrossVenueShortageOut])
def get_cross_venue_shortage(request, shortage_threshold: int = 1):
    cleanup_expired_reservations()

    venues = Venue.objects.filter(is_active=True)
    result = []

    for venue in venues:
        stations = ServiceStation.objects.filter(venue_id=venue.id, is_active=True)
        total_safety_stock = 0
        current_available = 0
        affected_stations = []
        urgent_need = 0

        for station in stations:
            station_available = Cart.objects.filter(
                station_id=station.id, status='available'
            ).exclude(status__in=['maintenance', 'scrapped']).count()
            station_shortage = max(0, station.safety_stock - station_available)

            total_safety_stock += station.safety_stock
            current_available += station_available

            if station_shortage > 0:
                if station_shortage >= station.safety_stock * 0.5:
                    urgent_need += station_shortage
                affected_stations.append({
                    'station_id': station.id,
                    'station_name': station.name,
                    'floor': station.floor,
                    'safety_stock': station.safety_stock,
                    'current_available': station_available,
                    'shortage': station_shortage,
                })

        total_shortage = max(0, total_safety_stock - current_available)

        if total_shortage >= shortage_threshold:
            result.append(CrossVenueShortageOut(
                venue_id=venue.id,
                venue_name=venue.name,
                total_safety_stock=total_safety_stock,
                current_available=current_available,
                shortage=total_shortage,
                urgent_need=urgent_need,
                affected_stations=sorted(affected_stations, key=lambda x: x['shortage'], reverse=True),
            ))

    result.sort(key=lambda x: x.shortage, reverse=True)
    return result


@router.get('/cross-venue-transfer-rate', response=CrossVenueTransferRateOut)
def get_cross_venue_transfer_rate(request, days: int = 30):
    cleanup_expired_reservations()
    now = timezone.now()
    start_time = now - timedelta(days=days)

    qs = CrossVenueTransfer.objects.filter(created_at__gte=start_time)
    total = qs.count()
    pending_approval = qs.filter(approval_status='pending').count()
    approved = qs.filter(approval_status='approved').count()
    rejected = qs.filter(approval_status='rejected').count()
    in_transit = qs.filter(transport_status='in_transit').count()
    arrived = qs.filter(transport_status='arrived').count()
    confirmed = qs.filter(transport_status='confirmed').count()
    urgent_count = qs.filter(priority='urgent').count()

    completed = qs.filter(transport_status='confirmed')
    completion_rate = round(confirmed / total * 100, 2) if total > 0 else 0.0

    total_hours = 0
    count = 0
    for t in completed:
        if t.shipped_at and t.confirmed_at:
            hours = (t.confirmed_at - t.shipped_at).total_seconds() / 3600
            total_hours += hours
            count += 1
    avg_transport_hours = round(total_hours / count, 2) if count > 0 else 0.0

    by_venue = []
    venues = Venue.objects.filter(is_active=True)
    for venue in venues:
        outgoing = qs.filter(from_venue_id=venue.id)
        incoming = qs.filter(to_venue_id=venue.id)
        out_total = outgoing.count()
        out_confirmed = outgoing.filter(transport_status='confirmed').count()
        out_rate = round(out_confirmed / out_total * 100, 2) if out_total > 0 else 0.0
        by_venue.append({
            'venue_id': venue.id,
            'venue_name': venue.name,
            'outgoing_total': out_total,
            'outgoing_confirmed': out_confirmed,
            'outgoing_completion_rate': out_rate,
            'incoming_total': incoming.count(),
            'incoming_pending': incoming.filter(transport_status__in=['in_transit', 'arrived']).count(),
        })

    return CrossVenueTransferRateOut(
        total_cross_transfers=total,
        pending_approval=pending_approval,
        approved=approved,
        rejected=rejected,
        in_transit=in_transit,
        arrived=arrived,
        confirmed=confirmed,
        completion_rate=completion_rate,
        urgent_count=urgent_count,
        avg_transport_hours=avg_transport_hours,
        by_venue=by_venue,
    )
