from django.contrib import admin

from .models import Parent


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "city", "created_at")
    search_fields = ("full_name", "email")
    ordering = ("full_name",)
