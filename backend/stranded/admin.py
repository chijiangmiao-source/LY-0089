from django.contrib import admin
from .models import StrandedRecord


@admin.register(StrandedRecord)
class StrandedRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'report_station', 'reporter_name', 'reporter_phone', 'status', 'reported_at', 'recycled_at', 'created_at']
    list_filter = ['status', 'report_station']
    search_fields = ['cart__cart_no', 'reporter_name', 'reporter_phone']
    readonly_fields = ['created_at', 'updated_at']
