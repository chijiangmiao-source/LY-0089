from django.db import models


class StrandedRecord(models.Model):
    STATUS_CHOICES = [
        ('reported', '已上报'),
        ('recycling', '回收中'),
        ('recycled', '已回收'),
    ]

    STATUS_DISPLAY = {
        'reported': '已上报',
        'recycling': '回收中',
        'recycled': '已回收',
    }

    cart = models.ForeignKey(
        'carts.Cart',
        on_delete=models.PROTECT,
        related_name='stranded_records',
        verbose_name='推车'
    )
    report_station = models.ForeignKey(
        'stations.ServiceStation',
        on_delete=models.PROTECT,
        related_name='stranded_reports',
        verbose_name='上报位置服务点'
    )
    reporter_name = models.CharField(max_length=50, null=True, blank=True, verbose_name='上报人姓名')
    reporter_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='上报人电话')
    description = models.TextField(null=True, blank=True, verbose_name='情况描述')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported', verbose_name='处理状态')
    reported_at = models.DateTimeField(verbose_name='上报时间')
    recycled_at = models.DateTimeField(null=True, blank=True, verbose_name='回收完成时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'stranded_records'
        verbose_name = '滞留记录'
        verbose_name_plural = verbose_name
        ordering = ['-reported_at']

    def __str__(self):
        return f'{self.cart.cart_no} - {self.get_status_display()}'

    @property
    def status_display(self):
        return self.STATUS_DISPLAY.get(self.status, self.status)
