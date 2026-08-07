from django.contrib import admin

from .models import Availability, LSAProfile, LSASkill, Skill


@admin.register(LSAProfile)
class LSAProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "hourly_rate", "rating", "is_active", "updated_at")
    search_fields = ("full_name",)
    list_filter = ("is_active",)
    ordering = ("full_name",)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(LSASkill)
class LSASkillAdmin(admin.ModelAdmin):
    list_display = ("lsa", "skill", "experience_years")
    autocomplete_fields = ("lsa", "skill")
    list_select_related = ("lsa", "skill")


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ("lsa", "date", "start_time", "end_time", "status")
    search_fields = ("lsa__full_name",)
    list_filter = ("date", "status")
    autocomplete_fields = ("lsa",)
    list_select_related = ("lsa",)
    ordering = ("date", "start_time")
