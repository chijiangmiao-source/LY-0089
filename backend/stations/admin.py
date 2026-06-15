from django.contrib import admin
from .models import ServiceStation


@admin.register(ServiceStation)
class ServiceStationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'floor', 'location', 'safety_stock', 'is_active', 'created_at')
    list_filter = ('floor', 'is_active')
    search_fields = ('name', 'location')
    readonly_fields = ('created_at', 'updated_at')
