from rest_framework import serializers
from .models import DonationDrive, DriveRegistration, DonationCertificate, DonorAvailabilitySlot


class DonationDriveSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source='organizer.username', read_only=True)
    remaining_slots = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    
    class Meta:
        model = DonationDrive
        fields = [
            'id',
            'title',
            'description',
            'organizer',
            'organizer_name',
            'city',
            'venue_name',
            'venue_address',
            'latitude',
            'longitude',
            'start_date',
            'end_date',
            'start_time',
            'end_time',
            'max_participants',
            'current_registrations',
            'target_units',
            'units_collected',
            'status',
            'banner_image',
            'contact_phone',
            'contact_email',
            'total_donors_attended',
            'total_successful_donations',
            'created_at',
            'updated_at',
            'remaining_slots',
            'completion_percentage',
            'is_full',
        ]
        read_only_fields = ['id', 'organizer', 'current_registrations', 'units_collected', 
                          'total_donors_attended', 'total_successful_donations', 'created_at', 'updated_at']
    
    def get_remaining_slots(self, obj):
        return obj.remaining_slots()
    
    def get_completion_percentage(self, obj):
        return obj.completion_percentage()
    
    def get_is_full(self, obj):
        return obj.is_full()


class DriveRegistrationSerializer(serializers.ModelSerializer):
    donor_name = serializers.CharField(source='donor.username', read_only=True)
    drive_title = serializers.CharField(source='drive.title', read_only=True)
    drive_details = DonationDriveSerializer(source='drive', read_only=True)
    
    class Meta:
        model = DriveRegistration
        fields = [
            'id',
            'drive',
            'donor',
            'status',
            'donated',
            'units_donated',
            'donation_completed_at',
            'reminder_sent_at',
            'confirmation_sent_at',
            'notes',
            'registered_at',
            'updated_at',
            'donor_name',
            'drive_title',
            'drive_details',
        ]
        read_only_fields = ['id', 'donor', 'registered_at', 'updated_at', 'reminder_sent_at', 'confirmation_sent_at']


class DonationCertificateSerializer(serializers.ModelSerializer):
    donor_name = serializers.CharField(source='donor.username', read_only=True)
    
    class Meta:
        model = DonationCertificate
        fields = [
            'id',
            'donor',
            'donor_name',
            'certificate_number',
            'drive_registration',
            'sos_response',
            'donation_date',
            'blood_group',
            'units_donated',
            'location',
            'qr_code_data',
            'pdf_url',
            'is_generated',
            'share_count',
            'issued_at',
        ]
        read_only_fields = ['id', 'donor', 'certificate_number', 'qr_code_data', 'issued_at']


class DonorAvailabilitySlotSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = DonorAvailabilitySlot
        fields = [
            'id',
            'donor',
            'date',
            'is_recurring',
            'day_of_week',
            'day_of_week_display',
            'start_time',
            'end_time',
            'is_all_day',
            'availability_type',
            'reason',
            'auto_response_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'donor', 'created_at', 'updated_at']
