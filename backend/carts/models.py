from django.db import models


class Cart(models.Model):
    CART_TYPE_CHOICES = [
        ('standard', '标准款'),
        ('large', '大号款'),
    ]

    STATUS_CHOICES = [
        ('available', '可用'),
        ('borrowed', '借出中'),
        ('stranded', '滞留'),
        ('transferring', '调拨中'),
        ('cleaning', '清洁中'),
        ('reset_check', '复位检查中'),
    ]

    STATUS_DISPLAY = {
        'available': '可用',
        'borrowed': '借出中',
        'stranded': '滞留',
        'transferring': '调拨中',
        'cleaning': '清洁中',
        'reset_check': '复位检查中',
    }

    cart_no = models.CharField(max_length=50, unique=True, verbose_name='推车编号')
    station = models.ForeignKey('stations.ServiceStation', on_delete=models.PROTECT, related_name='carts', null=True, blank=True, verbose_name='所属服务点')
    cart_type = models.CharField(max_length=20, choices=CART_TYPE_CHOICES, verbose_name='车型')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='当前状态')
    last_clean_time = models.DateTimeField(null=True, blank=True, verbose_name='最近清洁时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'carts'
        verbose_name = '推车档案'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.cart_no}'

    @property
    def status_display(self):
        return self.STATUS_DISPLAY.get(self.status, self.status)
