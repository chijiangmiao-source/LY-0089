from django.contrib import admin
from .models import CrossVenueTransfer


@admin.register(CrossVenueTransfer)
class CrossVenueTransferAdmin(admin.ModelAdmin):
    list_display = [
        'transfer_no', 'from_venue', 'to_venue', 'cart', 'priority',
        'approval_status', 'transport_status', 'created_at'
    ]
    list_filter = ['approval_status', 'transport_status', 'priority', 'from_venue', 'to_venue']
    search_fields = ['transfer_no', 'cart__cart_no']
