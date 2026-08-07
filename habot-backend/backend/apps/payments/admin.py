from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("gateway_reference", "booking", "amount", "status", "transaction_time")
    list_filter = ("status",)
    autocomplete_fields = ("booking",)
    list_select_related = ("booking",)
    readonly_fields = ("transaction_time",)
