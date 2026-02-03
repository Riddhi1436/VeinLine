from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'read_at',
            'priority',
            'action_url',
            'icon',
            'channels',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'read_at',
            'created_at',
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'id',
            'enable_in_app',
            'enable_email',
            'enable_sms',
            'enable_push',
            'notify_sos_requests',
            'notify_sos_responses',
            'notify_appointments',
            'notify_achievements',
            'notify_thank_you_messages',
            'notify_system_messages',
            'quiet_hours_start',
            'quiet_hours_end',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']
