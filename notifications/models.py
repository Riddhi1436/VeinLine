from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class NotificationType(models.TextChoices):
    """Types of notifications"""
    SOS_REQUEST = "sos_request", "New SOS Request"
    SOS_RESPONSE = "sos_response", "SOS Response Received"
    SOS_FULFILLED = "sos_fulfilled", "SOS Request Fulfilled"
    APPOINTMENT_REMINDER = "appointment_reminder", "Appointment Reminder"
    APPOINTMENT_CONFIRMED = "appointment_confirmed", "Appointment Confirmed"
    APPOINTMENT_CANCELLED = "appointment_cancelled", "Appointment Cancelled"
    NEW_BADGE = "new_badge", "Achievement Badge Earned"
    DONOR_THANK_YOU = "donor_thank_you", "Donor Thank You Message"
    ACTIVITY = "activity", "Activity Update"
    SYSTEM = "system", "System Message"


class NotificationChannel(models.TextChoices):
    """Notification delivery channels"""
    IN_APP = "in_app", "In-App"
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"
    PUSH = "push", "Push Notification"


class Notification(models.Model):
    """User notifications"""
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification type and content
    notification_type = models.CharField(max_length=32, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related object (generic foreign key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Channels (can be sent via multiple channels)
    channels = models.JSONField(default=list, help_text="List of channels: in_app, email, sms, push")
    
    # Metadata
    priority = models.CharField(
        max_length=16,
        choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')],
        default='normal'
    )
    action_url = models.CharField(max_length=255, blank=True, help_text="URL to navigate to when clicked")
    icon = models.CharField(max_length=64, blank=True, help_text="Emoji or icon to display")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self) -> str:
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class NotificationPreference(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Channel preferences
    enable_in_app = models.BooleanField(default=True)
    enable_email = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=True)
    enable_push = models.BooleanField(default=False)
    
    # Notification type preferences (quiet hours, opt-out, etc)
    notify_sos_requests = models.BooleanField(default=True)
    notify_sos_responses = models.BooleanField(default=True)
    notify_appointments = models.BooleanField(default=True)
    notify_achievements = models.BooleanField(default=True)
    notify_thank_you_messages = models.BooleanField(default=True)
    notify_system_messages = models.BooleanField(default=True)
    
    # Quiet hours (skip notifications between these times)
    quiet_hours_start = models.TimeField(null=True, blank=True, help_text="e.g., 22:00")
    quiet_hours_end = models.TimeField(null=True, blank=True, help_text="e.g., 08:00")
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"{self.user.username} - Notification Preferences"
    
    def should_notify(self, notification_type: str) -> bool:
        """Check if user wants notifications for this type"""
        pref_map = {
            NotificationType.SOS_REQUEST: self.notify_sos_requests,
            NotificationType.SOS_RESPONSE: self.notify_sos_responses,
            NotificationType.SOS_FULFILLED: self.notify_sos_responses,
            NotificationType.APPOINTMENT_REMINDER: self.notify_appointments,
            NotificationType.APPOINTMENT_CONFIRMED: self.notify_appointments,
            NotificationType.APPOINTMENT_CANCELLED: self.notify_appointments,
            NotificationType.NEW_BADGE: self.notify_achievements,
            NotificationType.DONOR_THANK_YOU: self.notify_thank_you_messages,
            NotificationType.SYSTEM: self.notify_system_messages,
        }
        return pref_map.get(notification_type, True)

