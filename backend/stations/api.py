from django.shortcuts import get_object_or_404
from ninja import Router, Query
from typing import List

from .models import ServiceStation
from .schemas import StationIn, StationOut
from carts.models import Cart
from reservations.utils import cleanup_expired_reservations

router = Router()


@router.get('/', response=List[StationOut])
def list_stations(request):
    cleanup_expired_reservations()
    stations = ServiceStation.objects.all()
    result = []
    for station in stations:
        current_count = Cart.objects.filter(station_id=station.id, status='available').count()
        station_data = {
            'id': station.id,
            'name': station.name,
            'floor': station.floor,
            'location': station.location,
            'safety_stock': station.safety_stock,
            'is_active': station.is_active,
            'current_count': current_count,
            'created_at': station.created_at,
            'updated_at': station.updated_at,
        }
        result.append(station_data)
    return result


@router.get('/{station_id}', response=StationOut)
def get_station(request, station_id: int):
    cleanup_expired_reservations()
    station = get_object_or_404(ServiceStation, id=station_id)
    current_count = Cart.objects.filter(station_id=station.id, status='available').count()
    return {
        'id': station.id,
        'name': station.name,
        'floor': station.floor,
        'location': station.location,
        'safety_stock': station.safety_stock,
        'is_active': station.is_active,
        'current_count': current_count,
        'created_at': station.created_at,
        'updated_at': station.updated_at,
    }


@router.post('/', response=StationOut)
def create_station(request, payload: StationIn):
    station = ServiceStation.objects.create(**payload.model_dump())
    current_count = Cart.objects.filter(station_id=station.id, status='available').count()
    return {
        'id': station.id,
        'name': station.name,
        'floor': station.floor,
        'location': station.location,
        'safety_stock': station.safety_stock,
        'is_active': station.is_active,
        'current_count': current_count,
        'created_at': station.created_at,
        'updated_at': station.updated_at,
    }


@router.put('/{station_id}', response=StationOut)
def update_station(request, station_id: int, payload: StationIn):
    station = get_object_or_404(ServiceStation, id=station_id)
    for attr, value in payload.model_dump().items():
        setattr(station, attr, value)
    station.save()
    current_count = Cart.objects.filter(station_id=station.id, status='available').count()
    return {
        'id': station.id,
        'name': station.name,
        'floor': station.floor,
        'location': station.location,
        'safety_stock': station.safety_stock,
        'is_active': station.is_active,
        'current_count': current_count,
        'created_at': station.created_at,
        'updated_at': station.updated_at,
    }


@router.delete('/{station_id}')
def delete_station(request, station_id: int):
    station = get_object_or_404(ServiceStation, id=station_id)
    station.delete()
    return {'success': True}
