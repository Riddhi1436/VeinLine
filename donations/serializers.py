from rest_framework import serializers

from .models import BloodBankInventory, DonorDetails, DonorStatistics, Badge, DonorFeedback


class DonorDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonorDetails
        fields = [
            "id",
            "user",
            "full_name",
            "age",
            "blood_group",
            "city",
            "area",
            "is_available",
            "last_donated_at",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class BloodBankInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodBankInventory
        fields = ["id", "city", "blood_group", "units_available", "updated_at"]
        read_only_fields = ["id", "updated_at"]


class DonorStatisticsSerializer(serializers.ModelSerializer):
    badges_display = serializers.SerializerMethodField()
    
    class Meta:
        model = DonorStatistics
        fields = [
            "id",
            "donor",
            "total_donations",
            "total_lives_saved",
            "sos_responses",
            "successful_sos_responses",
            "badges",
            "badges_display",
            "rank",
            "points",
            "current_donation_streak",
            "response_rate",
            "average_response_time_hours",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "donor",
            "badges",
            "rank",
            "points",
            "response_rate",
            "average_response_time_hours",
            "created_at",
            "updated_at",
        ]
    
    def get_badges_display(self, obj):
        return obj.get_badge_display()


class DonorFeedbackSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    patient_id = serializers.IntegerField(source='patient.id', read_only=True)
    rating_display = serializers.CharField(source='get_rating_display', read_only=True)
    
    class Meta:
        model = DonorFeedback
        fields = [
            'id',
            'donor',
            'patient',
            'patient_id',
            'patient_name',
            'sos_request',
            'rating',
            'rating_display',
            'message',
            'is_public',
            'created_at',
        ]
        read_only_fields = ['id', 'patient', 'created_at']

class LeaderboardSerializer(serializers.ModelSerializer):
    donor_name = serializers.CharField(source='donor.get_full_name', read_only=True)
    donor_id = serializers.IntegerField(source='donor.id', read_only=True)
    blood_group = serializers.SerializerMethodField()
    
    class Meta:
        model = DonorStatistics
        fields = [
            "rank",
            "donor_id",
            "donor_name",
            "blood_group",
            "total_donations",
            "points",
            "badges",
            "response_rate",
            "sos_responses",
        ]
        read_only_fields = fields
    
    def get_blood_group(self, obj):
        if hasattr(obj.donor, 'donor_details'):
            return obj.donor.donor_details.blood_group
        return None