from django.contrib import admin

from .models import BloodGroupCompatibility


@admin.register(BloodGroupCompatibility)
class BloodGroupCompatibilityAdmin(admin.ModelAdmin):
    list_display = ("donor_group", "recipient_group", "is_compatible")
    list_filter = ("donor_group", "recipient_group", "is_compatible")
    search_fields = ("donor_group", "recipient_group")
