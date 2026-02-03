from rest_framework import serializers

from .models import BloodGroupCompatibility, BloodBank


class BloodGroupCompatibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodGroupCompatibility
        fields = ["id", "donor_group", "recipient_group", "is_compatible"]


class BloodBankSerializer(serializers.ModelSerializer):
    is_open = serializers.SerializerMethodField()
    
    class Meta:
        model = BloodBank
        fields = [
            'id',
            'name',
            'city',
            'address',
            'phone',
            'email',
            'latitude',
            'longitude',
            'opening_time',
            'closing_time',
            'is_open',
            'description',
            'website',
            'is_active',
            'accepts_walk_in',
            'has_emergency_service',
        ]
        read_only_fields = ['id', 'is_open']
    
    def get_is_open(self, obj):
        return obj.is_open()
