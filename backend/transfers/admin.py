from django.contrib import admin
from .models import TransferOrder


@admin.register(TransferOrder)
class TransferOrderAdmin(admin.ModelAdmin):
    list_display = ['transfer_no', 'cart', 'from_station', 'to_station', 'status', 'priority', 'operator', 'created_at', 'started_at', 'completed_at']
    list_filter = ['status', 'priority', 'from_station', 'to_station']
    search_fields = ['transfer_no', 'cart__cart_no']
    readonly_fields = ['created_at', 'updated_at']
