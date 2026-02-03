from django.contrib import admin
from .models import DonationDrive, DriveRegistration, DonationCertificate, DonorAvailabilitySlot


@admin.register(DonationDrive)
class DonationDriveAdmin(admin.ModelAdmin):
    list_display = ['title', 'city', 'start_date', 'status', 'current_registrations', 'max_participants']
    list_filter = ['status', 'city', 'start_date']
    search_fields = ['title', 'city', 'venue_name']
    date_hierarchy = 'start_date'


@admin.register(DriveRegistration)
class DriveRegistrationAdmin(admin.ModelAdmin):
    list_display = ['donor', 'drive', 'status', 'donated', 'registered_at']
    list_filter = ['status', 'donated']
    search_fields = ['donor__username', 'drive__title']


@admin.register(DonationCertificate)
class DonationCertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'donor', 'donation_date', 'blood_group', 'units_donated']
    search_fields = ['certificate_number', 'donor__username']
    list_filter = ['blood_group', 'donation_date']


@admin.register(DonorAvailabilitySlot)
class DonorAvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ['donor', 'date', 'is_recurring', 'availability_type']
    list_filter = ['availability_type', 'is_recurring']
    search_fields = ['donor__username']
