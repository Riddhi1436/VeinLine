from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from datetime import datetime, timedelta


class AppointmentSlot(models.Model):
    """Available donation appointment slots at blood banks"""
    
    SLOT_STATUS = (
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    BLOOD_BANK_CHOICES = (
        ('red_crescent', 'Red Crescent Blood Bank'),
        ('city_hospital', 'City Hospital Blood Bank'),
        ('private_clinic', 'Private Clinic Blood Bank'),
        ('mobile_unit', 'Mobile Donation Unit'),
    )
    
    blood_bank = models.CharField(max_length=50, choices=BLOOD_BANK_CHOICES)
    city = models.CharField(max_length=64)
    address = models.CharField(max_length=255, blank=True)
    date = models.DateField(validators=[MinValueValidator(datetime.now().date())])
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_donors = models.PositiveIntegerField(default=10)
    booked_donors = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=SLOT_STATUS, default='available')
    notes = models.TextField(blank=True, help_text="Special instructions or requirements")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['date', 'city', 'status']),
        ]
    
    def __str__(self) -> str:
        return f"{self.blood_bank} - {self.date} {self.start_time}"
    
    def is_available_for_booking(self) -> bool:
        return self.status == 'available' and self.booked_donors < self.max_donors
    
    def remaining_slots(self) -> int:
        return self.max_donors - self.booked_donors


class Appointment(models.Model):
    """Donor appointment bookings"""
    
    APPOINTMENT_STATUS = (
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    )
    
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    slot = models.ForeignKey(AppointmentSlot, on_delete=models.CASCADE, related_name='appointments')
    status = models.CharField(max_length=16, choices=APPOINTMENT_STATUS, default='scheduled')
    
    # Pre-appointment questionnaire
    has_answered_health_questions = models.BooleanField(default=False)
    health_check_passed = models.BooleanField(default=False)
    
    # Confirmation
    is_confirmed_by_donor = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Completion
    donation_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    units_donated = models.PositiveSmallIntegerField(default=0, help_text="Units of blood donated (usually 1 unit = 450ml)")
    
    # Notifications
    reminder_sent_at = models.DateTimeField(null=True, blank=True, help_text="When reminder notification was sent")
    
    booked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('donor', 'slot')
        ordering = ['-booked_at']
        indexes = [
            models.Index(fields=['donor', 'status']),
            models.Index(fields=['slot', 'status']),
        ]
    
    def __str__(self) -> str:
        return f"{self.donor.username} - {self.slot.date} ({self.status})"
    
    def send_reminder(self):
        """Send reminder if appointment is within 24 hours"""
        from django.utils import timezone
        if (self.slot.date - timezone.now().date()).days == 1:
            self.reminder_sent_at = timezone.now()
            self.save()
            return True
        return False


class HealthQuestionnaire(models.Model):
    """Medical eligibility questionnaire responses"""
    
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='health_questionnaire')
    
    # Health questions
    has_fever = models.BooleanField(default=False)
    has_cold_or_cough = models.BooleanField(default=False)
    has_high_blood_pressure = models.BooleanField(default=False)
    has_diabetes = models.BooleanField(default=False)
    has_heart_condition = models.BooleanField(default=False)
    has_cancer = models.BooleanField(default=False)
    has_hiv_or_aids = models.BooleanField(default=False)
    has_hepatitis = models.BooleanField(default=False)
    has_bleeding_disorder = models.BooleanField(default=False)
    is_pregnant = models.BooleanField(default=False)
    is_breastfeeding = models.BooleanField(default=False)
    
    # Lifestyle questions
    recent_tattoo_or_piercing = models.BooleanField(default=False, help_text="In last 3 months")
    recent_surgery = models.BooleanField(default=False, help_text="In last 6 months")
    recent_blood_transfusion = models.BooleanField(default=False, help_text="In last 1 year")
    recent_vaccination = models.BooleanField(default=False, help_text="In last 2 weeks")
    takes_blood_thinners = models.BooleanField(default=False)
    takes_antibiotics = models.BooleanField(default=False)
    
    # Last donation
    last_donation_date = models.DateField(null=True, blank=True)
    
    # Additional info
    weight_kg = models.FloatField(null=True, blank=True, validators=[MinValueValidator(50.0)])
    hemoglobin_level = models.FloatField(null=True, blank=True)
    
    additional_notes = models.TextField(blank=True)
    
    is_eligible = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Health Questionnaires"
    
    def __str__(self) -> str:
        return f"Health Check - {self.appointment.donor.username}"
    
    def check_eligibility(self) -> bool:
        """Check if donor is eligible based on health answers"""
        # Major disqualifying conditions
        if self.has_hiv_or_aids or self.has_hepatitis or self.has_cancer or self.has_bleeding_disorder:
            return False
        
        # Temporary disqualifying conditions
        if self.has_fever or self.has_cold_or_cough or self.is_pregnant:
            return False
        
        # Recent procedures
        if self.recent_tattoo_or_piercing or self.recent_surgery or self.recent_blood_transfusion:
            return False
        
        # Weight requirement
        if self.weight_kg and self.weight_kg < 50:
            return False
        
        # Last donation was less than 56 days ago
        if self.last_donation_date:
            days_since_donation = (datetime.now().date() - self.last_donation_date).days
            if days_since_donation < 56:
                return False
        
        return True
