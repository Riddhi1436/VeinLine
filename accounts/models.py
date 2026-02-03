from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta


class UserRole(models.TextChoices):
    DONOR = "donor", "Donor"
    PATIENT = "patient", "Patient"
    ADMIN = "admin", "Admin"


class Profile(models.Model):
    """
    Extends Django's auth User with VeinLine-specific attributes and role.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=16, choices=UserRole.choices, default=UserRole.PATIENT)
    phone_e164 = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone number in E.164 format (+countrycode...). Stored but not exposed without consent.",
    )
    city = models.CharField(max_length=64, blank=True)
    area = models.CharField(max_length=64, blank=True)
    is_verified = models.BooleanField(default=False, help_text="Email/Phone verified via OTP")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role})"


class OTPVerification(models.Model):
    """
    Stores OTP codes for email/phone verification during registration.
    """

    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (VERIFIED, "Verified"),
        (EXPIRED, "Expired"),
    ]

    phone_e164 = models.CharField(max_length=20, blank=True, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    otp_code = models.CharField(max_length=6)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['phone_e164', 'status']),
            models.Index(fields=['email', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        contact = self.phone_e164 or self.email
        return f"OTP for {contact} ({self.status})"

    def is_valid(self) -> bool:
        """Check if OTP is still valid and not expired."""
        if self.status == self.VERIFIED:
            return False
        if timezone.now() > self.expires_at:
            self.status = self.EXPIRED
            self.save()
            return False
        if self.attempts >= self.max_attempts:
            self.status = self.EXPIRED
            self.save()
            return False
        return True

    def verify(self, provided_otp: str) -> tuple[bool, str]:
        """
        Verify the provided OTP.
        Returns: (is_valid, message)
        """
        if self.status == self.VERIFIED:
            return False, "OTP already verified"

        if timezone.now() > self.expires_at:
            self.status = self.EXPIRED
            self.save()
            return False, "OTP expired"

        if self.attempts >= self.max_attempts:
            self.status = self.EXPIRED
            self.save()
            return False, "Maximum verification attempts exceeded"

        self.attempts += 1
        self.save()

        if self.otp_code != provided_otp:
            remaining = self.max_attempts - self.attempts
            return False, f"Invalid OTP. {remaining} attempts remaining."

        self.status = self.VERIFIED
        self.verified_at = timezone.now()
        self.save()
        return True, "OTP verified successfully"

# Create your models here.
