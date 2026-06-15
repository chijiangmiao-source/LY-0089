from django.db import models


class RentalRecord(models.Model):
    STAGE_CHOICES = [
        ('borrowing', '借用中'),
        ('returned', '已归还'),
        ('overdue', '逾期未还'),
    ]

    STAGE_DISPLAY = {
        'borrowing': '借用中',
        'returned': '已归还',
        'overdue': '逾期未还',
    }

    rental_no = models.CharField(max_length=50, unique=True, verbose_name='借用单号')
    user_phone = models.CharField(max_length=20, verbose_name='借用人手机号')
    borrow_time = models.DateTimeField(verbose_name='借出时间')
    return_time = models.DateTimeField(null=True, blank=True, verbose_name='归还时间')
    borrow_station = models.ForeignKey(
        'stations.ServiceStation',
        on_delete=models.PROTECT,
        related_name='borrowed_records',
        verbose_name='借出服务点'
    )
    return_station = models.ForeignKey(
        'stations.ServiceStation',
        on_delete=models.PROTECT,
        related_name='returned_records',
        null=True,
        blank=True,
        verbose_name='归还服务点'
    )
    cart = models.ForeignKey('carts.Cart', on_delete=models.PROTECT, verbose_name='推车')
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, verbose_name='当前环节')
    is_overdue = models.BooleanField(default=False, verbose_name='是否逾期')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'rental_records'
        verbose_name = '借还记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.rental_no}'

    @property
    def stage_display(self):
        return self.STAGE_DISPLAY.get(self.stage, self.stage)
