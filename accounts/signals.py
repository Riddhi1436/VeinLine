from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, UserRole

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile when a User is created (for both regular and OAuth users)."""
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={'role': UserRole.PATIENT}  # Default role
        )
