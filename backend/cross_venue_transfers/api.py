from datetime import datetime
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import paginate
from typing import Optional

from .models import CrossVenueTransfer
from .schemas import (
    CrossVenueTransferCreateIn,
    CrossVenueTransferApprovalIn,
    CrossVenueTransportStartIn,
    CrossVenueTransferOut,
)
from carts.models import Cart
from venues.models import Venue


router = Router()


def generate_transfer_no() -> str:
    today = timezone.now().strftime('%Y%m%d')
    count = CrossVenueTransfer.objects.filter(created_at__date=timezone.now().date()).count() + 1
    return f'CVT-{today}-{count:04d}'


def cross_transfer_to_out(t: CrossVenueTransfer) -> CrossVenueTransferOut:
    return CrossVenueTransferOut(
        id=t.id,
        transfer_no=t.transfer_no,
        from_venue_id=t.from_venue_id,
        from_venue_name=t.from_venue.name if t.from_venue else '',
        to_venue_id=t.to_venue_id,
        to_venue_name=t.to_venue.name if t.to_venue else '',
        from_station_id=t.from_station_id,
        from_station_name=t.from_station.name if t.from_station else None,
        to_station_id=t.to_station_id,
        to_station_name=t.to_station.name if t.to_station else None,
        cart_id=t.cart_id,
        cart_no=t.cart.cart_no if t.cart else '',
        cart_type=t.cart_type,
        priority=t.priority,
        priority_display=t.priority_display,
        quantity=t.quantity,
        reason=t.reason,
        approval_status=t.approval_status,
        approval_status_display=t.approval_status_display,
        transport_status=t.transport_status,
        transport_status_display=t.transport_status_display,
        applicant_id=t.applicant_id,
        applicant_name=str(t.applicant) if t.applicant else None,
        approver_id=t.approver_id,
        approver_name=str(t.approver) if t.approver else None,
        approver_comment=t.approver_comment,
        approval_at=t.approval_at,
        transporter=t.transporter,
        transport_tracking_no=t.transport_tracking_no,
        shipped_at=t.shipped_at,
        arrived_at=t.arrived_at,
        confirmed_at=t.confirmed_at,
        confirmer_id=t.confirmer_id,
        confirmer_name=str(t.confirmer) if t.confirmer else None,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.get('/', response=list[CrossVenueTransferOut])
@paginate
def list_cross_transfers(
    request,
    from_venue_id: Optional[int] = None,
    to_venue_id: Optional[int] = None,
    approval_status: Optional[str] = None,
    transport_status: Optional[str] = None,
):
    queryset = CrossVenueTransfer.objects.select_related(
        'from_venue', 'to_venue', 'from_station', 'to_station', 'cart',
        'applicant', 'approver', 'confirmer'
    ).all()
    if from_venue_id is not None:
        queryset = queryset.filter(from_venue_id=from_venue_id)
    if to_venue_id is not None:
        queryset = queryset.filter(to_venue_id=to_venue_id)
    if approval_status is not None:
        queryset = queryset.filter(approval_status=approval_status)
    if transport_status is not None:
        queryset = queryset.filter(transport_status=transport_status)
    return [cross_transfer_to_out(t) for t in queryset]


@router.get('/all', response=list[CrossVenueTransferOut])
def list_all_cross_transfers(
    request,
    from_venue_id: Optional[int] = None,
    to_venue_id: Optional[int] = None,
    approval_status: Optional[str] = None,
    transport_status: Optional[str] = None,
):
    queryset = CrossVenueTransfer.objects.select_related(
        'from_venue', 'to_venue', 'from_station', 'to_station', 'cart',
        'applicant', 'approver', 'confirmer'
    ).all()
    if from_venue_id is not None:
        queryset = queryset.filter(from_venue_id=from_venue_id)
    if to_venue_id is not None:
        queryset = queryset.filter(to_venue_id=to_venue_id)
    if approval_status is not None:
        queryset = queryset.filter(approval_status=approval_status)
    if transport_status is not None:
        queryset = queryset.filter(transport_status=transport_status)
    return [cross_transfer_to_out(t) for t in queryset]


@router.get('/{transfer_id}', response=CrossVenueTransferOut)
def get_cross_transfer(request, transfer_id: int):
    t = get_object_or_404(CrossVenueTransfer.objects.select_related(
        'from_venue', 'to_venue', 'from_station', 'to_station', 'cart',
        'applicant', 'approver', 'confirmer'
    ), id=transfer_id)
    return cross_transfer_to_out(t)


@router.post('/', response=CrossVenueTransferOut)
def create_cross_transfer(request, payload: CrossVenueTransferCreateIn):
    cart = get_object_or_404(Cart.objects.select_related('station__venue'), id=payload.cart_id)
    if cart.status not in ('available', 'transferring'):
        raise HttpError(400, f'推车当前状态为{cart.status_display}，无法发起跨场地调拨')

    from_venue = get_object_or_404(Venue, id=payload.from_venue_id)
    to_venue = get_object_or_404(Venue, id=payload.to_venue_id)
    if from_venue_id == to_venue_id:
        raise HttpError(400, '申请场地和目标场地不能相同')

    t = CrossVenueTransfer.objects.create(
        transfer_no=generate_transfer_no(),
        from_venue_id=payload.from_venue_id,
        to_venue_id=payload.to_venue_id,
        from_station_id=payload.from_station_id,
        to_station_id=payload.to_station_id,
        cart_id=payload.cart_id,
        cart_type=cart.cart_type,
        priority=payload.priority,
        quantity=payload.quantity,
        reason=payload.reason,
        applicant=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
    )
    t.refresh_from_db()
    t = CrossVenueTransfer.objects.select_related(
        'from_venue', 'to_venue', 'from_station', 'to_station', 'cart',
        'applicant', 'approver', 'confirmer'
    ).get(id=t.id)
    return cross_transfer_to_out(t)


@router.post('/{transfer_id}/approve', response=CrossVenueTransferOut)
def approve_cross_transfer(request, transfer_id: int, payload: CrossVenueTransferApprovalIn):
    t = get_object_or_404(CrossVenueTransfer, id=transfer_id)
    if t.approval_status != 'pending':
        raise HttpError(400, '当前状态不允许审批')

    t.approval_status = payload.approval_status
    t.approver_comment = payload.approver_comment
    t.approver = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
    t.approval_at = timezone.now()

    if payload.approval_status == 'approved':
        t.cart.status = 'transferring'
        t.cart.save()

    t.save()
    t = CrossVenueTransfer.objects.select_related(
        'from_venue', 'to_venue', 'from_station', 'to_station', 'cart',
        'applicant', 'approver', 'confirmer'
    ).get(id=t.id)
    return cross_transfer_to_out(t)


@router.post('/{transfer_id}/start-transport', response=CrossVenueTransferOut)
def start_transport(request, transfer_id: int, payload: CrossVenueTransportStartIn):
    t = get_object_or_404(CrossVenueTransfer, id=transfer_id)
    if t.approval_status != 'approved':
        raise HttpError(400, '请先完成审批')
    if t.transport_status != 'not_started':
        raise HttpError(400, '当前运输状态不允许发货')

    t.transporter = payload.transporter
    t.transport_tracking_no = payload.transport_tracking_no
    t.transport_status = 'in_transit'
    t.shipped_at = timezone.now()
    t.save()
    t = CrossVenueTransfer.objects.select_related(
        'from_venue', 'to_venue', 'from_station', 'to_station', 'cart',
        'applicant', 'approver', 'confirmer'
    ).get(id=t.id)
    return cross_transfer_to_out(t)


@router.post('/{transfer_id}/mark-arrived', response=CrossVenueTransferOut)
def mark_arrived(request, transfer_id: int):
    t = get_object_or_404(CrossVenueTransfer, id=transfer_id)
    if t.transport_status != 'in_transit':
        raise HttpError(400, '当前运输状态不允许标记到达')

    t.transport_status = 'arrived'
    t.arrived_at = timezone.now()
    t.save()
    t = CrossVenueTransfer.objects.select_related(
        'from_venue', 'to_venue', 'from_station', 'to_station', 'cart',
        'applicant', 'approver', 'confirmer'
    ).get(id=t.id)
    return cross_transfer_to_out(t)


@router.post('/{transfer_id}/confirm-receipt', response=CrossVenueTransferOut)
def confirm_receipt(request, transfer_id: int):
    t = get_object_or_404(CrossVenueTransfer, id=transfer_id)
    if t.transport_status != 'arrived':
        raise HttpError(400, '当前运输状态不允许确认收货')

    t.transport_status = 'confirmed'
    t.confirmed_at = timezone.now()
    t.confirmer = request.user if hasattr(request, 'user') and request.user.is_authenticated else None

    if t.to_station_id:
        t.cart.station_id = t.to_station_id
    t.cart.status = 'available'
    t.cart.save()

    t.save()
    t = CrossVenueTransfer.objects.select_related(
        'from_venue', 'to_venue', 'from_station', 'to_station', 'cart',
        'applicant', 'approver', 'confirmer'
    ).get(id=t.id)
    return cross_transfer_to_out(t)


@router.post('/{transfer_id}/cancel', response=CrossVenueTransferOut)
def cancel_cross_transfer(request, transfer_id: int):
    t = get_object_or_404(CrossVenueTransfer, id=transfer_id)
    if t.approval_status == 'cancelled':
        raise HttpError(400, '调拨单已取消')
    if t.transport_status not in ('not_started',):
        raise HttpError(400, '运输已启动，无法取消')

    t.approval_status = 'cancelled'
    if t.cart.status == 'transferring':
        t.cart.status = 'available'
        t.cart.save()
    t.save()
    t = CrossVenueTransfer.objects.select_related(
        'from_venue', 'to_venue', 'from_station', 'to_station', 'cart',
        'applicant', 'approver', 'confirmer'
    ).get(id=t.id)
    return cross_transfer_to_out(t)


@router.get('/statistics/summary')
def get_cross_transfer_statistics(request):
    total = CrossVenueTransfer.objects.count()
    pending_approval = CrossVenueTransfer.objects.filter(approval_status='pending').count()
    approved = CrossVenueTransfer.objects.filter(approval_status='approved').count()
    rejected = CrossVenueTransfer.objects.filter(approval_status='rejected').count()
    in_transit = CrossVenueTransfer.objects.filter(transport_status='in_transit').count()
    arrived = CrossVenueTransfer.objects.filter(transport_status='arrived').count()
    confirmed = CrossVenueTransfer.objects.filter(transport_status='confirmed').count()
    urgent = CrossVenueTransfer.objects.filter(priority='urgent').count()

    completion_rate = round(confirmed / total * 100, 2) if total > 0 else 0.0

    return {
        'total': total,
        'pending_approval': pending_approval,
        'approved': approved,
        'rejected': rejected,
        'in_transit': in_transit,
        'arrived': arrived,
        'confirmed': confirmed,
        'urgent': urgent,
        'completion_rate': completion_rate,
    }
