import random
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from ninja import Router, Query
from ninja.errors import HttpError
from ninja.pagination import paginate

from .models import TransferOrder
from .schemas import TransferCreateIn, TransferOut
from carts.models import Cart
from stations.models import ServiceStation

router = Router()


def generate_transfer_no():
    now = timezone.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    return f'TF{timestamp}{random_suffix}'


def transfer_to_out(transfer: TransferOrder) -> TransferOut:
    return TransferOut(
        id=transfer.id,
        transfer_no=transfer.transfer_no,
        cart_id=transfer.cart_id,
        cart_no=transfer.cart.cart_no if transfer.cart else '',
        from_station_id=transfer.from_station_id,
        from_station_name=transfer.from_station.name if transfer.from_station else '',
        to_station_id=transfer.to_station_id,
        to_station_name=transfer.to_station.name if transfer.to_station else '',
        status=transfer.status,
        status_display=transfer.status_display,
        priority=transfer.priority,
        priority_display=transfer.priority_display,
        operator_id=transfer.operator_id,
        operator_name=str(transfer.operator) if transfer.operator else '',
        created_at=transfer.created_at,
        started_at=transfer.started_at,
        completed_at=transfer.completed_at,
    )


@router.get('/', response=list[TransferOut])
@paginate
def list_transfers(request, status: str = None, priority: str = None):
    queryset = TransferOrder.objects.select_related('cart', 'from_station', 'to_station', 'operator').all()
    if status:
        queryset = queryset.filter(status=status)
    if priority:
        queryset = queryset.filter(priority=priority)
    return [transfer_to_out(t) for t in queryset]


@router.get('/{transfer_id}', response=TransferOut)
def get_transfer(request, transfer_id: int):
    transfer = get_object_or_404(
        TransferOrder.objects.select_related('cart', 'from_station', 'to_station', 'operator'),
        id=transfer_id
    )
    return transfer_to_out(transfer)


@router.post('/', response=TransferOut)
@transaction.atomic
def create_transfer(request, payload: TransferCreateIn):
    cart = get_object_or_404(Cart, id=payload.cart_id)
    if cart.status == 'maintenance':
        raise HttpError(400, '该推车正在维修中，不允许调拨')
    if cart.status == 'scrapped':
        raise HttpError(400, '该推车已报废，不允许调拨')
    if cart.status != 'available':
        if cart.status == 'reserved':
            raise HttpError(400, '该推车已被预约，不允许调拨')
        raise HttpError(400, '推车当前状态不允许调拨')
    if payload.from_station_id == payload.to_station_id:
        raise HttpError(400, '源站和目标站不能相同')

    transfer_no = generate_transfer_no()
    transfer = TransferOrder.objects.create(
        transfer_no=transfer_no,
        cart_id=payload.cart_id,
        from_station_id=payload.from_station_id,
        to_station_id=payload.to_station_id,
        status='pending',
        priority=payload.priority or 'normal',
        operator=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
    )

    cart.status = 'transferring'
    cart.station = None
    cart.save()

    transfer = TransferOrder.objects.select_related('cart', 'from_station', 'to_station', 'operator').get(id=transfer.id)
    return transfer_to_out(transfer)


@router.put('/{transfer_id}/start', response=TransferOut)
@transaction.atomic
def start_transfer(request, transfer_id: int):
    transfer = get_object_or_404(
        TransferOrder.objects.select_related('cart', 'from_station', 'to_station', 'operator'),
        id=transfer_id
    )
    if transfer.status != 'pending':
        raise HttpError(400, '只有待出发状态的调拨单可以开始')
    transfer.status = 'transiting'
    transfer.started_at = timezone.now()
    transfer.save()
    return transfer_to_out(transfer)


@router.put('/{transfer_id}/complete', response=TransferOut)
@transaction.atomic
def complete_transfer(request, transfer_id: int):
    transfer = get_object_or_404(
        TransferOrder.objects.select_related('cart', 'from_station', 'to_station', 'operator'),
        id=transfer_id
    )
    if transfer.status != 'transiting':
        raise HttpError(400, '只有运输中状态的调拨单可以完成')
    transfer.status = 'completed'
    transfer.completed_at = timezone.now()
    transfer.save()

    cart = transfer.cart
    cart.status = 'available'
    cart.station = transfer.to_station
    cart.save()

    return transfer_to_out(transfer)


@router.put('/{transfer_id}/cancel', response=TransferOut)
@transaction.atomic
def cancel_transfer(request, transfer_id: int):
    transfer = get_object_or_404(
        TransferOrder.objects.select_related('cart', 'from_station', 'to_station', 'operator'),
        id=transfer_id
    )
    if transfer.status not in ['pending', 'transiting']:
        raise HttpError(400, '只有待出发或运输中状态的调拨单可以取消')
    transfer.status = 'cancelled'
    transfer.save()

    cart = transfer.cart
    cart.status = 'available'
    cart.station = transfer.from_station
    cart.save()

    return transfer_to_out(transfer)


@router.get('/priority-queue')
def get_priority_queue(request):
    stations = ServiceStation.objects.filter(is_active=True)
    result = []
    for station in stations:
        current_count = Cart.objects.filter(
            station_id=station.id, status='available'
        ).exclude(status__in=['maintenance', 'scrapped']).count()
        shortage = station.safety_stock - current_count
        if shortage > 0:
            recommended_source = None
            source_stations = ServiceStation.objects.filter(is_active=True).exclude(id=station.id)
            max_surplus = 0
            for src in source_stations:
                src_count = Cart.objects.filter(
                    station_id=src.id, status='available'
                ).exclude(status__in=['maintenance', 'scrapped']).count()
                surplus = src_count - src.safety_stock
                if surplus > max_surplus:
                    max_surplus = surplus
                    recommended_source = {
                        'id': src.id,
                        'name': src.name,
                        'floor': src.floor,
                        'surplus': surplus,
                    }
            result.append({
                'station_id': station.id,
                'station_name': station.name,
                'floor': station.floor,
                'safety_stock': station.safety_stock,
                'current_count': current_count,
                'shortage': shortage,
                'recommended_source': recommended_source,
            })
    result.sort(key=lambda x: x['shortage'], reverse=True)
    return result
