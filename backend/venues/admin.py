from django.contrib import admin
from .models import Venue


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['name', 'venue_type', 'address', 'is_active', 'created_at']
    list_filter = ['venue_type', 'is_active']
    search_fields = ['name', 'address']
