from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from reservations.models import CartReservation


class Command(BaseCommand):
    help = '自动释放超时未取车的预约推车'

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(f'开始检查过期预约，当前时间: {now}')

        expired_reservations = CartReservation.objects.filter(
            status='active',
            expire_time__lt=now
        ).select_related('cart')

        count = 0
        with transaction.atomic():
            for reservation in expired_reservations:
                reservation.status = 'expired'
                reservation.save()

                if reservation.cart:
                    reservation.cart.status = 'available'
                    reservation.cart.save()

                count += 1
                self.stdout.write(
                    f'  释放预约 {reservation.reservation_no} '
                    f'(用户: {reservation.user_phone}, '
                    f'推车: {reservation.cart.cart_no if reservation.cart else "无"})'
                )

        self.stdout.write(self.style.SUCCESS(f'处理完成，共释放 {count} 个过期预约'))
