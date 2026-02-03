"""
Deprecated stray module — disabled to avoid conflicts
"""
# This module was a stray file; templatetags are now in accounts/templatetags package
register = None

# Disabled

def safe_profile_role(user):
    """
    Safely get user role from profile.
    Returns the role if profile exists, otherwise returns 'guest'
    """
    if user and hasattr(user, "profile"):
        return getattr(user.profile, "role", "guest")
    return "guest"


@register.filter(name="safe_profile_city")
def safe_profile_city(user):
    """
    Safely get user city from profile.
    Returns the city if profile exists, otherwise returns empty string
    """
    if user and hasattr(user, "profile"):
        return getattr(user.profile, "city", "")
    return ""


@register.filter(name="safe_profile_area")
def safe_profile_area(user):
    """
    Safely get user area from profile.
    Returns the area if profile exists, otherwise returns empty string
    """
    if user and hasattr(user, "profile"):
        return getattr(user.profile, "area", "")
    return ""


@register.filter(name="safe_profile_phone")
def safe_profile_phone(user):
    """
    Safely get user phone from profile.
    Returns the phone if profile exists, otherwise returns empty string
    """
    if user and hasattr(user, "profile"):
        return getattr(user.profile, "phone_e164", "")
    return ""


@register.filter(name="is_donor")
def is_donor(user):
    """
    Check if user is a donor.
    Returns True only if authenticated and has donor role
    """
    if user and user.is_authenticated and hasattr(user, "profile"):
        return user.profile.role == "donor"
    return False


@register.filter(name="is_patient")
def is_patient(user):
    """
    Check if user is a patient.
    Returns True only if authenticated and has patient role
    """
    if user and user.is_authenticated and hasattr(user, "profile"):
        return user.profile.role == "patient"
    return False


@register.filter(name="has_profile")
def has_profile(user):
    """
    Check if user has a profile.
    Returns True if user is authenticated and has profile
    """
    if user and user.is_authenticated:
        return hasattr(user, "profile")
    return False


@register.simple_tag(name="user_profile_role")
def user_profile_role(user, default="guest"):
    """
    Template tag to safely get user role.
    Usage: {% user_profile_role user "guest" %}
    """
    if user and user.is_authenticated and hasattr(user, "profile"):
        return user.profile.role
    return default


@register.simple_tag(name="user_role_label")
def user_role_label(user):
    """
    Template tag to get user role with emoji.
    Usage: {% user_role_label user %}
    """
    if not user or not user.is_authenticated:
        return "👤 Guest"
    
    if not hasattr(user, "profile"):
        return "👤 User"
    
    role = user.profile.role
    labels = {
        "donor": "🩸 Donor",
        "patient": "🏥 Patient",
        "admin": "⚙️ Admin"
    }
    return labels.get(role, f"👤 {role.title()}")
