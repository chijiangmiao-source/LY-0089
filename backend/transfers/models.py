from django.db import models


class TransferOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', '待出发'),
        ('transiting', '运输中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    STATUS_DISPLAY = {
        'pending': '待出发',
        'transiting': '运输中',
        'completed': '已完成',
        'cancelled': '已取消',
    }

    PRIORITY_CHOICES = [
        ('normal', '普通'),
        ('urgent', '紧急'),
    ]

    PRIORITY_DISPLAY = {
        'normal': '普通',
        'urgent': '紧急',
    }

    transfer_no = models.CharField(max_length=50, unique=True, verbose_name='调拨单号')
    cart = models.ForeignKey('carts.Cart', on_delete=models.PROTECT, related_name='transfers', verbose_name='推车')
    from_station = models.ForeignKey('stations.ServiceStation', on_delete=models.PROTECT, related_name='outgoing_transfers', verbose_name='源站')
    to_station = models.ForeignKey('stations.ServiceStation', on_delete=models.PROTECT, related_name='incoming_transfers', verbose_name='目标站')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='调拨状态')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal', verbose_name='优先级')
    operator = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers', verbose_name='操作人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'transfer_orders'
        verbose_name = '跨点调拨单'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.transfer_no

    @property
    def status_display(self):
        return self.STATUS_DISPLAY.get(self.status, self.status)

    @property
    def priority_display(self):
        return self.PRIORITY_DISPLAY.get(self.priority, self.priority)
