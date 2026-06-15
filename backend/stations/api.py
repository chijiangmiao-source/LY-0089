from django.shortcuts import get_object_or_404
from ninja import Router, Query
from typing import List, Optional

from .models import ServiceStation
from .schemas import StationIn, StationOut
from carts.models import Cart
from reservations.utils import cleanup_expired_reservations

router = Router()


def station_to_out(station: ServiceStation) -> dict:
    current_count = Cart.objects.filter(
        station_id=station.id,
        status='available'
    ).exclude(
        status__in=['maintenance', 'scrapped']
    ).count()
    return {
        'id': station.id,
        'venue_id': station.venue_id,
        'venue_name': station.venue.name if station.venue else None,
        'name': station.name,
        'floor': station.floor,
        'location': station.location,
        'safety_stock': station.safety_stock,
        'is_active': station.is_active,
        'current_count': current_count,
        'created_at': station.created_at,
        'updated_at': station.updated_at,
    }


@router.get('/', response=List[StationOut])
def list_stations(request, venue_id: Optional[int] = None):
    cleanup_expired_reservations()
    queryset = ServiceStation.objects.select_related('venue').all()
    if venue_id is not None:
        queryset = queryset.filter(venue_id=venue_id)
    return [station_to_out(s) for s in queryset]


@router.get('/all', response=List[StationOut])
def list_all_stations(request, venue_id: Optional[int] = None, is_active: bool = None):
    cleanup_expired_reservations()
    queryset = ServiceStation.objects.select_related('venue').all()
    if venue_id is not None:
        queryset = queryset.filter(venue_id=venue_id)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    return [station_to_out(s) for s in queryset.order_by('venue_id', 'floor', 'name')]


@router.get('/{station_id}', response=StationOut)
def get_station(request, station_id: int):
    cleanup_expired_reservations()
    station = get_object_or_404(ServiceStation.objects.select_related('venue'), id=station_id)
    return station_to_out(station)


@router.post('/', response=StationOut)
def create_station(request, payload: StationIn):
    station = ServiceStation.objects.create(**payload.model_dump())
    station.refresh_from_db()
    return station_to_out(station)


@router.put('/{station_id}', response=StationOut)
def update_station(request, station_id: int, payload: StationIn):
    station = get_object_or_404(ServiceStation, id=station_id)
    for attr, value in payload.model_dump().items():
        setattr(station, attr, value)
    station.save()
    station.refresh_from_db()
    return station_to_out(station)


@router.delete('/{station_id}')
def delete_station(request, station_id: int):
    station = get_object_or_404(ServiceStation, id=station_id)
    station.delete()
    return {'success': True}
