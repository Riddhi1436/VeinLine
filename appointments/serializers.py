from rest_framework import serializers
from .models import AppointmentSlot, Appointment, HealthQuestionnaire


class AppointmentSlotSerializer(serializers.ModelSerializer):
    remaining_slots = serializers.SerializerMethodField()
    is_available_for_booking = serializers.SerializerMethodField()
    
    class Meta:
        model = AppointmentSlot
        fields = [
            'id',
            'blood_bank',
            'city',
            'address',
            'date',
            'start_time',
            'end_time',
            'max_donors',
            'booked_donors',
            'remaining_slots',
            'is_available_for_booking',
            'status',
            'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'booked_donors', 'created_at']
    
    def get_remaining_slots(self, obj):
        return obj.remaining_slots()
    
    def get_is_available_for_booking(self, obj):
        return obj.is_available_for_booking()


class HealthQuestionnaireSerializer(serializers.ModelSerializer):
    is_eligible = serializers.SerializerMethodField()
    
    class Meta:
        model = HealthQuestionnaire
        fields = [
            'id',
            'has_fever',
            'has_cold_or_cough',
            'has_high_blood_pressure',
            'has_diabetes',
            'has_heart_condition',
            'has_cancer',
            'has_hiv_or_aids',
            'has_hepatitis',
            'has_bleeding_disorder',
            'is_pregnant',
            'is_breastfeeding',
            'recent_tattoo_or_piercing',
            'recent_surgery',
            'recent_blood_transfusion',
            'recent_vaccination',
            'takes_blood_thinners',
            'takes_antibiotics',
            'last_donation_date',
            'weight_kg',
            'hemoglobin_level',
            'additional_notes',
            'is_eligible',
        ]
        read_only_fields = ['id', 'is_eligible']
    
    def get_is_eligible(self, obj):
        return obj.check_eligibility()
    
    def create(self, validated_data):
        questionnaire = super().create(validated_data)
        questionnaire.is_eligible = questionnaire.check_eligibility()
        questionnaire.save()
        return questionnaire
    
    def update(self, instance, validated_data):
        questionnaire = super().update(instance, validated_data)
        questionnaire.is_eligible = questionnaire.check_eligibility()
        questionnaire.save()
        return questionnaire


class AppointmentSerializer(serializers.ModelSerializer):
    slot_details = AppointmentSlotSerializer(source='slot', read_only=True)
    health_questionnaire = HealthQuestionnaireSerializer(read_only=True)
    slot_id = serializers.PrimaryKeyRelatedField(
        queryset=AppointmentSlot.objects.all(),
        write_only=True,
        source='slot'
    )
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'donor',
            'slot_id',
            'slot_details',
            'status',
            'has_answered_health_questions',
            'health_check_passed',
            'is_confirmed_by_donor',
            'confirmed_at',
            'donation_completed',
            'completed_at',
            'units_donated',
            'reminder_sent_at',
            'health_questionnaire',
            'booked_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'donor',
            'status',
            'health_check_passed',
            'confirmed_at',
            'completed_at',
            'reminder_sent_at',
            'health_questionnaire',
            'booked_at',
            'updated_at',
        ]
    
    def create(self, validated_data):
        validated_data['donor'] = self.context['request'].user
        return super().create(validated_data)
