from django.contrib import admin
from .models import CartReservation


@admin.register(CartReservation)
class CartReservationAdmin(admin.ModelAdmin):
    list_display = (
        'reservation_no',
        'user_phone',
        'station',
        'cart',
        'reserve_time',
        'expire_time',
        'status',
    )
    list_filter = ('status', 'station')
    search_fields = ('reservation_no', 'user_phone')
    ordering = ('-reserve_time',)
