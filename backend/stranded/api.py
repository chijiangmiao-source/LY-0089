from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from ninja import Router, Query
from ninja.errors import HttpError
from ninja.pagination import paginate

from .models import StrandedRecord
from .schemas import StrandedReportIn, StrandedOut
from carts.models import Cart

router = Router()


def stranded_to_out(record: StrandedRecord) -> StrandedOut:
    now = timezone.now()
    if record.recycled_at:
        duration = (record.recycled_at - record.reported_at).total_seconds() / 3600
    else:
        duration = (now - record.reported_at).total_seconds() / 3600

    return StrandedOut(
        id=record.id,
        cart_id=record.cart_id,
        cart_no=record.cart.cart_no if record.cart else '',
        report_station_id=record.report_station_id,
        report_station_name=record.report_station.name if record.report_station else '',
        reporter_name=record.reporter_name,
        reporter_phone=record.reporter_phone,
        description=record.description,
        status=record.status,
        status_display=record.status_display,
        reported_at=record.reported_at,
        recycled_at=record.recycled_at,
        duration_hours=round(duration, 2),
    )


@router.get('/', response=list[StrandedOut])
@paginate
def list_stranded(request, status: str = None):
    queryset = StrandedRecord.objects.select_related('cart', 'report_station').all()
    if status:
        queryset = queryset.filter(status=status)
    return [stranded_to_out(r) for r in queryset]


@router.get('/{record_id}', response=StrandedOut)
def get_stranded(request, record_id: int):
    record = get_object_or_404(
        StrandedRecord.objects.select_related('cart', 'report_station'),
        id=record_id
    )
    return stranded_to_out(record)


@router.post('/report', response=StrandedOut)
@transaction.atomic
def report_stranded(request, payload: StrandedReportIn):
    cart = get_object_or_404(Cart, id=payload.cart_id)
    if cart.status == 'maintenance':
        raise HttpError(400, '维修中的推车不能上报滞留')
    if cart.status == 'scrapped':
        raise HttpError(400, '已报废的推车不能上报滞留')
    if cart.status == 'transferring':
        raise HttpError(400, '调拨中的推车不能上报滞留')
    if cart.status == 'reserved':
        raise HttpError(400, '已预约的推车不能上报滞留')

    now = timezone.now()
    record = StrandedRecord.objects.create(
        cart_id=payload.cart_id,
        report_station_id=payload.report_station_id,
        reporter_name=payload.reporter_name,
        reporter_phone=payload.reporter_phone,
        description=payload.description,
        status='reported',
        reported_at=now,
    )

    cart.status = 'stranded'
    cart.save()

    record = StrandedRecord.objects.select_related('cart', 'report_station').get(id=record.id)
    return stranded_to_out(record)


@router.put('/{record_id}/recycle', response=StrandedOut)
@transaction.atomic
def mark_recycling(request, record_id: int):
    record = get_object_or_404(
        StrandedRecord.objects.select_related('cart', 'report_station'),
        id=record_id
    )
    if record.status != 'reported':
        raise HttpError(400, '只有已上报状态的记录可以标记回收中')
    record.status = 'recycling'
    record.save()
    return stranded_to_out(record)


@router.put('/{record_id}/complete', response=StrandedOut)
@transaction.atomic
def complete_recycle(request, record_id: int):
    record = get_object_or_404(
        StrandedRecord.objects.select_related('cart', 'report_station'),
        id=record_id
    )
    if record.status != 'recycling':
        raise HttpError(400, '只有回收中状态的记录可以完成回收')

    now = timezone.now()
    record.status = 'recycled'
    record.recycled_at = now
    record.save()

    cart = record.cart
    cart.status = 'cleaning'
    cart.save()

    return stranded_to_out(record)


@router.delete('/{record_id}')
def delete_stranded(request, record_id: int):
    record = get_object_or_404(StrandedRecord, id=record_id)
    record.delete()
    return {'success': True}
