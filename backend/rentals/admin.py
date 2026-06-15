from django.contrib import admin
from .models import RentalRecord


@admin.register(RentalRecord)
class RentalRecordAdmin(admin.ModelAdmin):
    list_display = ['rental_no', 'user_phone', 'cart', 'stage', 'borrow_station', 'return_station', 'borrow_time', 'return_time', 'created_at', 'updated_at']
    list_filter = ['stage', 'borrow_station', 'return_station']
    search_fields = ['rental_no', 'user_phone']
    readonly_fields = ['created_at', 'updated_at']
