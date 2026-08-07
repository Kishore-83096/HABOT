from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "parent", "availability", "status", "created_at")
    search_fields = ("parent__full_name", "parent__email")
    list_filter = ("status",)
    autocomplete_fields = ("parent", "availability")
    list_select_related = ("parent", "availability")
    readonly_fields = ("created_at", "updated_at")
