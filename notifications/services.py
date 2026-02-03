"""
Notification service for creating and sending notifications
"""
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from .models import Notification, NotificationType, NotificationChannel

User = get_user_model()


class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    def create_notification(
        recipient,
        notification_type: str,
        title: str,
        message: str,
        channels: list = None,
        priority: str = 'normal',
        action_url: str = '',
        icon: str = '',
        content_object=None
    ) -> Notification:
        """
        Create and send a notification
        
        Args:
            recipient: User object who receives the notification
            notification_type: Type from NotificationType
            title: Notification title
            message: Notification message
            channels: List of channels (in_app, email, sms, push)
            priority: Priority level (low, normal, high, urgent)
            action_url: URL to navigate to
            icon: Emoji or icon
            content_object: Related object (SOS, Appointment, etc.)
        """
        if channels is None:
            channels = [NotificationChannel.IN_APP]
        
        # Get content type if object is provided
        content_type = None
        object_id = None
        if content_object:
            content_type = ContentType.objects.get_for_model(content_object)
            object_id = content_object.id
        
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            channels=channels,
            priority=priority,
            action_url=action_url,
            icon=icon,
            content_type=content_type,
            object_id=object_id,
        )
        
        # Send via channels
        NotificationService._send_via_channels(notification, channels)
        
        return notification
    
    @staticmethod
    def _send_via_channels(notification: Notification, channels: list):
        """Send notification via specified channels"""
        for channel in channels:
            if channel == NotificationChannel.IN_APP:
                # Already saved to DB
                pass
            elif channel == NotificationChannel.EMAIL:
                NotificationService._send_email(notification)
            elif channel == NotificationChannel.SMS:
                NotificationService._send_sms(notification)
            elif channel == NotificationChannel.PUSH:
                NotificationService._send_push(notification)
    
    @staticmethod
    def _send_email(notification: Notification):
        """Send email notification"""
        # TODO: Implement email sending
        from core.services.emailing import send_email
        
        try:
            send_email(
                to_email=notification.recipient.email,
                subject=notification.title,
                body=notification.message,
            )
        except Exception as e:
            print(f"Error sending email notification: {e}")
    
    @staticmethod
    def _send_sms(notification: Notification):
        """Send SMS notification"""
        # TODO: Implement SMS sending
        try:
            from core.services.sms import send_sms
            from accounts.models import Profile
            
            profile = Profile.objects.get(user=notification.recipient)
            if profile.phone_e164:
                send_sms(
                    phone=profile.phone_e164,
                    message=f"{notification.title}: {notification.message[:160]}"
                )
        except Exception as e:
            print(f"Error sending SMS notification: {e}")
    
    @staticmethod
    def _send_push(notification: Notification):
        """Send push notification"""
        # TODO: Implement push notification (Firebase, etc.)
        pass
    
    @staticmethod
    def notify_new_sos_request(sos_request, donors):
        """Notify donors about new SOS request"""
        message = f"New blood request: {sos_request.blood_group_needed} in {sos_request.city}"
        
        for donor in donors:
            NotificationService.create_notification(
                recipient=donor,
                notification_type=NotificationType.SOS_REQUEST,
                title="🚨 New SOS Request",
                message=message,
                channels=[NotificationChannel.IN_APP, NotificationChannel.SMS],
                priority='urgent',
                action_url=f'/sos/{sos_request.id}/',
                icon='🚨',
                content_object=sos_request,
            )
    
    @staticmethod
    def notify_sos_response(sos_response):
        """Notify patient about SOS response"""
        donor_name = sos_response.donor.get_full_name() or sos_response.donor.username
        message = f"{donor_name} has responded to your SOS request"
        
        NotificationService.create_notification(
            recipient=sos_response.request.requester,
            notification_type=NotificationType.SOS_RESPONSE,
            title="✅ SOS Response Received",
            message=message,
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            priority='high',
            action_url=f'/sos/{sos_response.request.id}/',
            icon='✅',
            content_object=sos_response,
        )
    
    @staticmethod
    def notify_appointment_reminder(appointment):
        """Send appointment reminder (24 hours before)"""
        donor_name = appointment.slot.blood_bank
        message = f"Reminder: You have a donation appointment at {donor_name} tomorrow at {appointment.slot.start_time}"
        
        NotificationService.create_notification(
            recipient=appointment.donor,
            notification_type=NotificationType.APPOINTMENT_REMINDER,
            title="📅 Appointment Reminder",
            message=message,
            channels=[NotificationChannel.IN_APP, NotificationChannel.SMS, NotificationChannel.EMAIL],
            priority='high',
            action_url=f'/appointments/{appointment.id}/',
            icon='📅',
            content_object=appointment,
        )
    
    @staticmethod
    def notify_appointment_confirmed(appointment):
        """Notify donor when appointment is confirmed"""
        message = f"Your donation appointment at {appointment.slot.blood_bank} on {appointment.slot.date} is confirmed"
        
        NotificationService.create_notification(
            recipient=appointment.donor,
            notification_type=NotificationType.APPOINTMENT_CONFIRMED,
            title="✅ Appointment Confirmed",
            message=message,
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            priority='normal',
            action_url=f'/appointments/{appointment.id}/',
            icon='✅',
            content_object=appointment,
        )
    
    @staticmethod
    def notify_new_badge(donor, badge_name):
        """Notify donor about new badge achievement"""
        message = f"Congratulations! You've earned the '{badge_name}' badge"
        
        NotificationService.create_notification(
            recipient=donor,
            notification_type=NotificationType.NEW_BADGE,
            title="🎖️ Achievement Unlocked",
            message=message,
            channels=[NotificationChannel.IN_APP],
            priority='normal',
            action_url='/leaderboard/',
            icon='🎖️',
        )
    
    @staticmethod
    def notify_thank_you_message(donor, patient_name, message):
        """Notify donor about thank you message from patient"""
        NotificationService.create_notification(
            recipient=donor,
            notification_type=NotificationType.DONOR_THANK_YOU,
            title="💌 Thank You Message",
            message=f"{patient_name} sent you a thank you message",
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            priority='normal',
            action_url='/feedback/',
            icon='💌',
        )
