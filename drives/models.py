from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from datetime import datetime


class DriveStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ONGOING = "ongoing", "Ongoing"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class DonationDrive(models.Model):
    """Blood donation drives/events"""
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organized_drives")
    
    # Location
    city = models.CharField(max_length=64)
    venue_name = models.CharField(max_length=200)
    venue_address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Date and time
    start_date = models.DateField(validators=[MinValueValidator(datetime.now().date())])
    end_date = models.DateField(validators=[MinValueValidator(datetime.now().date())])
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Capacity
    max_participants = models.PositiveIntegerField(default=50)
    current_registrations = models.PositiveIntegerField(default=0)
    
    # Blood requirements
    target_units = models.PositiveIntegerField(default=20, help_text="Target blood units to collect")
    units_collected = models.PositiveIntegerField(default=0)
    
    # Status
    status = models.CharField(max_length=16, choices=DriveStatus.choices, default=DriveStatus.DRAFT)
    
    # Media
    banner_image = models.URLField(blank=True)
    
    # Organizer contact
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Statistics
    total_donors_attended = models.PositiveIntegerField(default=0)
    total_successful_donations = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date', '-start_time']
        indexes = [
            models.Index(fields=['city', 'status', 'start_date']),
            models.Index(fields=['status', 'start_date']),
        ]
    
    def __str__(self) -> str:
        return f"{self.title} - {self.city} ({self.start_date})"
    
    def is_full(self) -> bool:
        return self.current_registrations >= self.max_participants
    
    def remaining_slots(self) -> int:
        return max(0, self.max_participants - self.current_registrations)
    
    def completion_percentage(self) -> float:
        if self.target_units == 0:
            return 0.0
        return min(100.0, (self.units_collected / self.target_units) * 100)


class RegistrationStatus(models.TextChoices):
    REGISTERED = "registered", "Registered"
    CONFIRMED = "confirmed", "Confirmed"
    ATTENDED = "attended", "Attended"
    NO_SHOW = "no_show", "No Show"
    CANCELLED = "cancelled", "Cancelled"


class DriveRegistration(models.Model):
    """Registration for donation drives"""
    
    drive = models.ForeignKey(DonationDrive, on_delete=models.CASCADE, related_name="registrations")
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="drive_registrations")
    
    status = models.CharField(max_length=16, choices=RegistrationStatus.choices, default=RegistrationStatus.REGISTERED)
    
    # Donation details (filled after drive)
    donated = models.BooleanField(default=False)
    units_donated = models.PositiveSmallIntegerField(default=0)
    donation_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notifications
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Additional notes
    notes = models.TextField(blank=True)
    
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('drive', 'donor')
        ordering = ['-registered_at']
        indexes = [
            models.Index(fields=['drive', 'status']),
            models.Index(fields=['donor', 'status']),
        ]
    
    def __str__(self) -> str:
        return f"{self.donor.username} -> {self.drive.title} ({self.status})"


class DonationCertificate(models.Model):
    """Donation certificates for donors"""
    
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    
    # Certificate details
    certificate_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Related donation
    drive_registration = models.ForeignKey(DriveRegistration, on_delete=models.SET_NULL, null=True, blank=True, related_name="certificate")
    sos_response = models.ForeignKey('sos.SOSResponse', on_delete=models.SET_NULL, null=True, blank=True, related_name="certificate")
    
    # Certificate info
    donation_date = models.DateField()
    blood_group = models.CharField(max_length=3)
    units_donated = models.PositiveSmallIntegerField(default=1)
    location = models.CharField(max_length=200)
    
    # QR code for verification
    qr_code_data = models.TextField(help_text="QR code content for verification")
    
    # PDF generation
    pdf_url = models.URLField(blank=True)
    is_generated = models.BooleanField(default=False)
    
    # Sharing
    share_count = models.PositiveIntegerField(default=0)
    
    issued_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['donor', '-issued_at']),
            models.Index(fields=['certificate_number']),
        ]
    
    def __str__(self) -> str:
        return f"Certificate {self.certificate_number} - {self.donor.username}"
    
    def generate_certificate_number(self):
        """Generate unique certificate number"""
        import secrets
        from django.utils import timezone
        year = timezone.now().year
        random_part = secrets.token_hex(4).upper()
        return f"VL-{year}-{random_part}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_number:
            self.certificate_number = self.generate_certificate_number()
        super().save(*args, **kwargs)


class DonorAvailabilitySlot(models.Model):
    """Donor availability calendar"""
    
    AVAILABILITY_TYPE = (
        ('available', 'Available'),
        ('unavailable', 'Unavailable'),
        ('vacation', 'Vacation Mode'),
    )
    
    DAY_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="availability_slots")
    
    # Date-based availability
    date = models.DateField(null=True, blank=True, help_text="Specific date (leave blank for recurring)")
    
    # Recurring availability
    is_recurring = models.BooleanField(default=False)
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_OF_WEEK, null=True, blank=True)
    
    # Time slots
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    # All-day availability
    is_all_day = models.BooleanField(default=True)
    
    # Status
    availability_type = models.CharField(max_length=16, choices=AVAILABILITY_TYPE, default='available')
    
    # Reason for unavailability
    reason = models.CharField(max_length=200, blank=True)
    
    # Auto-responder message
    auto_response_message = models.TextField(blank=True, help_text="Message sent when unavailable")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['donor', 'date']),
            models.Index(fields=['donor', 'is_recurring', 'day_of_week']),
        ]
    
    def __str__(self) -> str:
        if self.is_recurring:
            return f"{self.donor.username} - {self.get_day_of_week_display()} ({self.availability_type})"
        return f"{self.donor.username} - {self.date} ({self.availability_type})"
