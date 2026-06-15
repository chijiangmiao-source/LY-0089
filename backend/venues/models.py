from django.db import models


class Venue(models.Model):
    VENUE_TYPE_CHOICES = [
        ('mall', '商场'),
        ('park', '园区'),
        ('other', '其他'),
    ]

    VENUE_TYPE_DISPLAY = {
        'mall': '商场',
        'park': '园区',
        'other': '其他',
    }

    name = models.CharField(max_length=100, unique=True, verbose_name='场地名称')
    venue_type = models.CharField(max_length=20, choices=VENUE_TYPE_CHOICES, default='mall', verbose_name='场地类型')
    address = models.CharField(max_length=255, verbose_name='地址')
    contact_person = models.CharField(max_length=50, null=True, blank=True, verbose_name='联系人')
    contact_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='联系电话')
    total_floors = models.IntegerField(default=5, verbose_name='总楼层数')
    description = models.TextField(null=True, blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'venues'
        verbose_name = '场地'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def venue_type_display(self):
        return self.VENUE_TYPE_DISPLAY.get(self.venue_type, self.venue_type)
