from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from ninja import Router, Query
from ninja.errors import HttpError
from ninja.pagination import paginate

from .models import MaintenanceRecord
from .schemas import MaintenanceCreateIn, MaintenanceUpdateIn, MaintenanceOut
from carts.models import Cart
from stations.models import ServiceStation
from reservations.utils import cleanup_expired_reservations

router = Router()


def maintenance_to_out(record: MaintenanceRecord) -> MaintenanceOut:
    return MaintenanceOut(
        id=record.id,
        cart_id=record.cart_id,
        cart_no=record.cart.cart_no,
        fault_type=record.fault_type,
        fault_type_display=record.fault_type_display,
        report_station_id=record.report_station_id,
        report_station_name=record.report_station.name if record.report_station else '',
        reporter_name=record.reporter_name,
        description=record.description,
        status=record.status,
        status_display=record.status_display,
        repair_result=record.repair_result,
        reported_at=record.reported_at,
        started_at=record.started_at,
        completed_at=record.completed_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get('/', response=list[MaintenanceOut])
@paginate
def list_maintenance(request, status: str = None, fault_type: str = None):
    cleanup_expired_reservations()
    queryset = MaintenanceRecord.objects.select_related('cart', 'report_station').all()
    if status:
        queryset = queryset.filter(status=status)
    if fault_type:
        queryset = queryset.filter(fault_type=fault_type)
    return [maintenance_to_out(r) for r in queryset]


@router.get('/{record_id}', response=MaintenanceOut)
def get_maintenance(request, record_id: int):
    cleanup_expired_reservations()
    record = get_object_or_404(
        MaintenanceRecord.objects.select_related('cart', 'report_station'),
        id=record_id
    )
    return maintenance_to_out(record)


@router.post('/', response=MaintenanceOut)
@transaction.atomic
def create_maintenance(request, payload: MaintenanceCreateIn):
    cleanup_expired_reservations()
    cart = get_object_or_404(Cart, id=payload.cart_id)
    
    if cart.status in ['maintenance', 'scrapped']:
        raise HttpError(400, '该推车已在维修中或已报废')

    report_station = get_object_or_404(ServiceStation, id=payload.report_station_id)

    record = MaintenanceRecord.objects.create(
        cart=cart,
        fault_type=payload.fault_type,
        report_station=report_station,
        reporter_name=payload.reporter_name,
        description=payload.description,
        status='pending',
        reported_at=timezone.now(),
    )

    cart.status = 'maintenance'
    cart.save()

    record.refresh_from_db()
    record = MaintenanceRecord.objects.select_related('cart', 'report_station').get(id=record.id)
    return maintenance_to_out(record)


@router.put('/{record_id}/start', response=MaintenanceOut)
@transaction.atomic
def start_maintenance(request, record_id: int):
    record = get_object_or_404(
        MaintenanceRecord.objects.select_related('cart', 'report_station'),
        id=record_id
    )
    if record.status != 'pending':
        raise HttpError(400, '只有待维修状态的维修单可以开始维修')

    record.status = 'repairing'
    record.started_at = timezone.now()
    record.save()
    return maintenance_to_out(record)


@router.put('/{record_id}/complete', response=MaintenanceOut)
@transaction.atomic
def complete_maintenance(request, record_id: int, payload: MaintenanceUpdateIn):
    record = get_object_or_404(
        MaintenanceRecord.objects.select_related('cart', 'report_station'),
        id=record_id
    )
    if record.status != 'repairing':
        raise HttpError(400, '只有维修中状态的维修单可以完成')

    record.status = 'completed'
    record.repair_result = payload.repair_result
    record.completed_at = timezone.now()
    record.save()

    cart = record.cart
    cart.status = 'available'
    cart.save()

    return maintenance_to_out(record)


@router.put('/{record_id}/scrap', response=MaintenanceOut)
@transaction.atomic
def scrap_cart(request, record_id: int, payload: MaintenanceUpdateIn):
    record = get_object_or_404(
        MaintenanceRecord.objects.select_related('cart', 'report_station'),
        id=record_id
    )
    if record.status not in ['pending', 'repairing']:
        raise HttpError(400, '只有待维修或维修中的维修单可以转为报废')

    record.status = 'scrapped'
    record.repair_result = payload.repair_result
    record.completed_at = timezone.now()
    record.save()

    cart = record.cart
    cart.status = 'scrapped'
    cart.save()

    return maintenance_to_out(record)
