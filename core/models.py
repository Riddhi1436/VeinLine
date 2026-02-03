from django.db import models

from .constants import BloodGroup


class BloodGroupCompatibility(models.Model):
    """
    Rule-based compatibility table: donor blood group -> recipient blood group.
    Useful for admin management and matching queries.
    """

    donor_group = models.CharField(max_length=3, choices=BloodGroup.CHOICES)
    recipient_group = models.CharField(max_length=3, choices=BloodGroup.CHOICES)
    is_compatible = models.BooleanField(default=False)

    class Meta:
        unique_together = ("donor_group", "recipient_group")
        indexes = [
            models.Index(fields=["donor_group", "recipient_group"]),
            models.Index(fields=["recipient_group", "is_compatible"]),
        ]

    def __str__(self) -> str:
        return f"{self.donor_group} -> {self.recipient_group}: {'YES' if self.is_compatible else 'NO'}"


class BloodBank(models.Model):
    """Blood donation centers/banks"""
    
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=64)
    address = models.CharField(max_length=500)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Operating hours
    opening_time = models.TimeField(default="08:00")
    closing_time = models.TimeField(default="18:00")
    
    # Info
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Services
    accepts_walk_in = models.BooleanField(default=True)
    has_emergency_service = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['city', 'name']
        indexes = [
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} - {self.city}"
    
    def is_open(self):
        """Check if blood bank is currently open"""
        from django.utils import timezone
        now = timezone.now().time()
        return self.opening_time <= now <= self.closing_time

