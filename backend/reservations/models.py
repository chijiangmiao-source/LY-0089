from django.db import models
from django.utils import timezone


class CartReservation(models.Model):
    STATUS_CHOICES = [
        ('active', '预约中'),
        ('completed', '已完成'),
        ('expired', '已失效'),
        ('cancelled', '已取消'),
    ]

    STATUS_DISPLAY = {
        'active': '预约中',
        'completed': '已完成',
        'expired': '已失效',
        'cancelled': '已取消',
    }

    reservation_no = models.CharField(max_length=50, unique=True, verbose_name='预约单号')
    user_phone = models.CharField(max_length=20, verbose_name='预约人手机号')
    station = models.ForeignKey(
        'stations.ServiceStation',
        on_delete=models.PROTECT,
        related_name='reservations',
        verbose_name='预约服务点'
    )
    cart = models.ForeignKey(
        'carts.Cart',
        on_delete=models.PROTECT,
        related_name='reservations',
        null=True,
        blank=True,
        verbose_name='预约推车'
    )
    reserve_time = models.DateTimeField(verbose_name='预约时间')
    expire_time = models.DateTimeField(verbose_name='失效时间')
    pickup_time = models.DateTimeField(null=True, blank=True, verbose_name='取车时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='预约状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'cart_reservations'
        verbose_name = '推车预约记录'
        verbose_name_plural = verbose_name
        ordering = ['-reserve_time']

    def __str__(self):
        return f'{self.reservation_no} - {self.user_phone}'

    @property
    def status_display(self):
        return self.STATUS_DISPLAY.get(self.status, self.status)

    @property
    def is_expired(self):
        return timezone.now() > self.expire_time
