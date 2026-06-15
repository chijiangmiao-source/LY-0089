from django.contrib import admin
from .models import MaintenanceRecord


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'cart', 'fault_type_display', 'status_display',
        'report_station', 'reported_at', 'completed_at'
    ]
    list_filter = ['status', 'fault_type', 'reported_at']
    search_fields = ['cart__cart_no', 'description', 'repair_result']
    raw_id_fields = ['cart', 'report_station']
    readonly_fields = ['created_at', 'updated_at']
