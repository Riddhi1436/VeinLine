from django.contrib import admin

from .models import BloodBankInventory, DonorDetails


@admin.register(DonorDetails)
class DonorDetailsAdmin(admin.ModelAdmin):
    list_display = ("full_name", "blood_group", "city", "area", "is_available", "updated_at")
    list_filter = ("blood_group", "city", "is_available")
    search_fields = ("full_name", "city", "area", "user__username", "user__email")


@admin.register(BloodBankInventory)
class BloodBankInventoryAdmin(admin.ModelAdmin):
    list_display = ("city", "blood_group", "units_available", "updated_at")
    list_filter = ("city", "blood_group")
    search_fields = ("city",)
