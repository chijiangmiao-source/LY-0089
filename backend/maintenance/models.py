from django.db import models


class MaintenanceRecord(models.Model):
    FAULT_TYPE_CHOICES = [
        ('wheel', '车轮故障'),
        ('brake', '刹车故障'),
        ('seat', '座椅故障'),
        ('handle', '把手故障'),
        ('lock', '锁具故障'),
        ('frame', '车架故障'),
        ('other', '其他故障'),
    ]

    STATUS_CHOICES = [
        ('pending', '待维修'),
        ('repairing', '维修中'),
        ('completed', '维修完成'),
        ('scrapped', '已报废'),
    ]

    STATUS_DISPLAY = {
        'pending': '待维修',
        'repairing': '维修中',
        'completed': '维修完成',
        'scrapped': '已报废',
    }

    FAULT_TYPE_DISPLAY = {
        'wheel': '车轮故障',
        'brake': '刹车故障',
        'seat': '座椅故障',
        'handle': '把手故障',
        'lock': '锁具故障',
        'frame': '车架故障',
        'other': '其他故障',
    }

    cart = models.ForeignKey(
        'carts.Cart',
        on_delete=models.PROTECT,
        related_name='maintenance_records',
        verbose_name='推车'
    )
    fault_type = models.CharField(
        max_length=20,
        choices=FAULT_TYPE_CHOICES,
        verbose_name='故障类型'
    )
    report_station = models.ForeignKey(
        'stations.ServiceStation',
        on_delete=models.PROTECT,
        related_name='maintenance_reports',
        verbose_name='报修服务点'
    )
    reporter_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='报修人姓名'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='故障描述'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='处理状态'
    )
    repair_result = models.TextField(
        null=True,
        blank=True,
        verbose_name='维修结果'
    )
    reported_at = models.DateTimeField(
        verbose_name='报修时间'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='开始维修时间'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='完成时间'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'maintenance_records'
        verbose_name = '维修记录'
        verbose_name_plural = verbose_name
        ordering = ['-reported_at']

    def __str__(self):
        return f'维修单#{self.id} - {self.cart.cart_no}'

    @property
    def status_display(self):
        return self.STATUS_DISPLAY.get(self.status, self.status)

    @property
    def fault_type_display(self):
        return self.FAULT_TYPE_DISPLAY.get(self.fault_type, self.fault_type)
