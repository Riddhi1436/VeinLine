import secrets

from django.conf import settings
from django.db import models

from core.constants import BloodGroup


class SOSStatus(models.TextChoices):
    OPEN = "open", "Open"
    FULFILLED = "fulfilled", "Fulfilled"
    CANCELLED = "cancelled", "Cancelled"


class SOSPriority(models.TextChoices):
    NORMAL = "normal", "Normal"
    URGENT = "urgent", "Urgent (24 hours)"
    CRITICAL = "critical", "Critical (Immediate)"


class SOSRequest(models.Model):
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sos_requests")
    blood_group_needed = models.CharField(max_length=3, choices=BloodGroup.CHOICES)
    units_needed = models.PositiveSmallIntegerField(default=1)
    city = models.CharField(max_length=64)
    area = models.CharField(max_length=64, blank=True)
    hospital_name = models.CharField(max_length=120, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=SOSStatus.choices, default=SOSStatus.OPEN)
    priority = models.CharField(max_length=16, choices=SOSPriority.choices, default=SOSPriority.NORMAL)

    # Used for SMS replies without requiring login. Rotatable if abused.
    sms_reply_token = models.CharField(max_length=32, default="", blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "blood_group_needed", "city"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["priority", "status"]),
        ]

    def ensure_sms_token(self):
        if not self.sms_reply_token:
            self.sms_reply_token = secrets.token_hex(8)

    def save(self, *args, **kwargs):
        self.ensure_sms_token()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"SOS #{self.id} {self.blood_group_needed} in {self.city} ({self.status})"
    
    def get_priority_icon(self):
        icons = {
            SOSPriority.NORMAL: '🔵',
            SOSPriority.URGENT: '🟠',
            SOSPriority.CRITICAL: '🔴',
        }
        return icons.get(self.priority, '🔵')


class ResponseChoice(models.TextChoices):
    YES = "yes", "Yes"
    NO = "no", "No"
    PENDING = "pending", "Pending"


class ResponseChannel(models.TextChoices):
    WEB = "web", "Web"
    SMS = "sms", "SMS"


class SOSResponse(models.Model):
    request = models.ForeignKey(SOSRequest, on_delete=models.CASCADE, related_name="responses")
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sos_responses")

    response = models.CharField(max_length=16, choices=ResponseChoice.choices, default=ResponseChoice.PENDING)
    channel = models.CharField(max_length=8, choices=ResponseChannel.choices, default=ResponseChannel.WEB)

    # Privacy: contact revealed only after explicit donor consent for this request.
    donor_consented_to_share_contact = models.BooleanField(default=False)
    patient_contact_revealed_at = models.DateTimeField(null=True, blank=True)

    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("request", "donor")
        indexes = [
            models.Index(fields=["request", "response"]),
            models.Index(fields=["donor", "response"]),
        ]

    def __str__(self) -> str:
        return f"SOSResponse req={self.request_id} donor={self.donor_id} {self.response}"


class DonationStatus(models.TextChoices):
    AGREED = "agreed", "Agreed to Donate"
    TRAVELING = "traveling", "Traveling to Location"
    ARRIVED = "arrived", "Arrived at Location"
    DONATING = "donating", "Donation in Progress"
    COMPLETED = "completed", "Donation Completed"
    CANCELLED = "cancelled", "Cancelled"


class DonationTracker(models.Model):
    """Real-time tracking of donation progress"""
    
    sos_response = models.OneToOneField(SOSResponse, on_delete=models.CASCADE, related_name="donation_tracker")
    current_status = models.CharField(max_length=16, choices=DonationStatus.choices, default=DonationStatus.AGREED)
    
    # Location tracking (optional, with donor consent)
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Estimated arrival
    estimated_arrival_time = models.DateTimeField(null=True, blank=True)
    
    # Status timestamps
    agreed_at = models.DateTimeField(auto_now_add=True)
    traveling_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    donating_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    notes = models.TextField(blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["sos_response", "current_status"]),
        ]
    
    def __str__(self) -> str:
        return f"Tracker for SOS Response #{self.sos_response_id} - {self.current_status}"
    
    def update_status(self, new_status: str):
        """Update status and set appropriate timestamp"""
        from django.utils import timezone
        self.current_status = new_status
        
        if new_status == DonationStatus.TRAVELING and not self.traveling_at:
            self.traveling_at = timezone.now()
        elif new_status == DonationStatus.ARRIVED and not self.arrived_at:
            self.arrived_at = timezone.now()
        elif new_status == DonationStatus.DONATING and not self.donating_at:
            self.donating_at = timezone.now()
        elif new_status == DonationStatus.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        
        self.save()


class Message(models.Model):
    """Secure messaging between patients and donors"""
    
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_messages")
    
    # Link to SOS conversation context
    sos_request = models.ForeignKey(SOSRequest, on_delete=models.CASCADE, related_name="messages", null=True, blank=True)
    
    content = models.TextField()
    
    # Message templates
    is_template_message = models.BooleanField(default=False)
    template_type = models.CharField(max_length=32, blank=True, choices=[
        ('on_my_way', 'On My Way'),
        ('arrived', 'Arrived'),
        ('need_directions', 'Need Directions'),
        ('thank_you', 'Thank You'),
    ])
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['sender', 'recipient', '-created_at']),
            models.Index(fields=['sos_request', '-created_at']),
        ]
    
    def __str__(self) -> str:
        return f"Message from {self.sender.username} to {self.recipient.username}"
    
    def mark_as_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class EmergencyContact(models.Model):
    """Trusted emergency contacts who can make SOS requests on behalf of user"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="emergency_contacts")
    
    # Contact can be another user in the system or external
    contact_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="emergency_contact_for")
    
    # If not a system user
    contact_name = models.CharField(max_length=120, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    relationship = models.CharField(max_length=50, help_text="e.g., Family, Friend, Caregiver")
    
    # Permissions
    can_create_sos = models.BooleanField(default=True)
    can_view_medical_info = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'contact_user')
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self) -> str:
        contact_display = self.contact_user.username if self.contact_user else self.contact_name
        return f"Emergency Contact: {contact_display} for {self.user.username}"

# Create your models here.
