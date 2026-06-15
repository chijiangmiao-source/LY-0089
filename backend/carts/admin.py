from django.contrib import admin
from .models import Cart


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['cart_no', 'station', 'cart_type', 'status', 'last_clean_time', 'created_at', 'updated_at']
    list_filter = ['cart_type', 'status', 'station']
    search_fields = ['cart_no']
    readonly_fields = ['created_at', 'updated_at']
