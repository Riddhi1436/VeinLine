from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpRequest

from .models import Profile, UserRole


class AccountAdapter(DefaultAccountAdapter):
    """Custom account adapter for regular registration."""
    
    def is_open_for_signup(self, request: HttpRequest):
        return True


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom social account adapter for OAuth users."""
    
    def is_open_for_signup(self, request: HttpRequest, sociallogin):
        return True
    
    def save_user(self, request, sociallogin, form=None):
        """Save user from social login and create profile."""
        user = super().save_user(request, sociallogin, form)
        
        # Ensure profile exists for OAuth users
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            Profile.objects.create(
                user=user,
                role=UserRole.DONOR  # Default role for OAuth users
            )
        
        return user
    
    def pre_social_login(self, request, sociallogin):
        """Handle existing users logging in with Google."""
        if sociallogin.is_existing:
            return
        
        # Check if user with this email already exists
        if sociallogin.email_addresses:
            email = sociallogin.email_addresses[0]
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(email=email.email)
                # Connect the social account to existing user
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass

