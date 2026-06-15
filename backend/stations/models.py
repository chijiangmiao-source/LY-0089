from django.db import models


class ServiceStation(models.Model):
    venue = models.ForeignKey('venues.Venue', on_delete=models.PROTECT, related_name='stations', null=True, blank=True, verbose_name='所属场地')
    name = models.CharField(max_length=100, verbose_name='服务点名')
    floor = models.IntegerField(verbose_name='楼层')
    location = models.CharField(max_length=255, verbose_name='位置描述')
    safety_stock = models.IntegerField(default=5, verbose_name='安全保有量')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'service_stations'
        verbose_name = '服务点'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
