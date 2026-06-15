from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from reservations.models import CartReservation


CLEANUP_CACHE_KEY = 'reservation_cleanup_last_run'
CLEANUP_INTERVAL_SECONDS = 30


@transaction.atomic
def cleanup_expired_reservations(force: bool = False) -> int:
    now = timezone.now()

    if not force:
        last_run = cache.get(CLEANUP_CACHE_KEY)
        if last_run and (now - last_run).total_seconds() < CLEANUP_INTERVAL_SECONDS:
            return 0

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

    cache.set(CLEANUP_CACHE_KEY, now, CLEANUP_INTERVAL_SECONDS)
    return count
