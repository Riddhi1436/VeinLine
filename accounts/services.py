"""
OTP generation, verification, and delivery services for registration.
"""

import logging
import random
from datetime import timedelta

from django.utils import timezone
from core.services.sms import send_sms
from core.services.emailing import send_fallback_email
from .models import OTPVerification

logger = logging.getLogger(__name__)


def generate_otp_code(length: int = 6) -> str:
    """
    Generate a random OTP code.
    
    Args:
        length: Number of digits in OTP (default 6)
    
    Returns:
        OTP code as string
    """
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def create_or_update_otp(phone_e164: str = "", email: str = "", validity_minutes: int = 10) -> OTPVerification:
    """
    Create or update an OTP record for phone or email verification.
    
    Args:
        phone_e164: Phone number in E.164 format
        email: Email address
        validity_minutes: How long OTP is valid (default 10 minutes)
    
    Returns:
        OTPVerification object
    
    Raises:
        ValueError: If both phone and email are empty
    """
    if not phone_e164 and not email:
        raise ValueError("Either phone_e164 or email must be provided")

    otp_code = generate_otp_code()
    expires_at = timezone.now() + timedelta(minutes=validity_minutes)

    if phone_e164:
        otp, created = OTPVerification.objects.update_or_create(
            phone_e164=phone_e164,
            defaults={
                "otp_code": otp_code,
                "status": OTPVerification.PENDING,
                "attempts": 0,
                "expires_at": expires_at,
                "verified_at": None,
                "email": "",
            }
        )
        logger.info(f"OTP created for phone {phone_e164} (created={created})")
    else:
        otp, created = OTPVerification.objects.update_or_create(
            email=email,
            defaults={
                "otp_code": otp_code,
                "status": OTPVerification.PENDING,
                "attempts": 0,
                "expires_at": expires_at,
                "verified_at": None,
                "phone_e164": "",
            }
        )
        logger.info(f"OTP created for email {email} (created={created})")

    return otp


def send_otp_via_sms(phone_e164: str, otp_code: str) -> dict:
    """
    Send OTP to phone via SMS.
    
    Args:
        phone_e164: Phone number in E.164 format
        otp_code: OTP code to send
    
    Returns:
        SMS delivery result dictionary
    """
    message = f"Your VeinLine registration OTP is: {otp_code}. Valid for 10 minutes. Do not share this code."
    
    result = send_sms(phone_e164, message)
    logger.info(f"OTP SMS sent to {phone_e164}: {result}")
    
    return result


def send_otp_via_email(email: str, otp_code: str) -> int:
    """
    Send OTP to email address.
    
    Args:
        email: Email address
        otp_code: OTP code to send
    
    Returns:
        Number of emails sent
    """
    subject = "VeinLine Registration OTP"
    message = f"""
Your VeinLine registration OTP is: {otp_code}

This code is valid for 10 minutes. Do not share this code with anyone.

If you didn't request this registration, please ignore this email.

Best regards,
VeinLine Team
    """.strip()

    result = send_fallback_email(email, subject, message)
    logger.info(f"OTP email sent to {email}: {result} email(s) sent")
    
    return result


def send_otp(phone_e164: str = "", email: str = "") -> dict:
    """
    Send OTP via SMS and/or Email based on provided contact.
    
    Args:
        phone_e164: Phone number in E.164 format
        email: Email address
    
    Returns:
        Dictionary with delivery status
    
    Raises:
        ValueError: If both phone and email are empty
    """
    if not phone_e164 and not email:
        raise ValueError("Either phone_e164 or email must be provided")

    otp = create_or_update_otp(phone_e164=phone_e164, email=email)
    result = {
        "otp_id": otp.id,
        "contact": phone_e164 or email,
        "delivery": {}
    }

    if phone_e164:
        result["delivery"]["sms"] = send_otp_via_sms(phone_e164, otp.otp_code)
    
    if email:
        result["delivery"]["email"] = send_otp_via_email(email, otp.otp_code)

    return result


def verify_otp(phone_e164: str = "", email: str = "", provided_otp: str = "") -> tuple[bool, str]:
    """
    Verify OTP provided by user.
    
    Args:
        phone_e164: Phone number in E.164 format
        email: Email address
        provided_otp: OTP code provided by user
    
    Returns:
        (is_verified, message)
    """
    if not phone_e164 and not email:
        return False, "Either phone_e164 or email must be provided"

    contact = phone_e164 or email
    try:
        if phone_e164:
            otp_record = OTPVerification.objects.get(phone_e164=phone_e164)
        else:
            otp_record = OTPVerification.objects.get(email=email)
    except OTPVerification.DoesNotExist:
        logger.warning(f"OTP record not found for {contact}")
        return False, "No OTP request found. Please request a new OTP."

    is_valid, message = otp_record.verify(provided_otp)
    
    if is_valid:
        logger.info(f"OTP verified successfully for {contact}")
    else:
        logger.warning(f"OTP verification failed for {contact}: {message}")
    
    return is_valid, message


def cleanup_expired_otps():
    """
    Delete OTP records that have expired (older than 24 hours).
    Can be called periodically via management command.
    """
    cutoff = timezone.now() - timedelta(hours=24)
    deleted_count, _ = OTPVerification.objects.filter(
        created_at__lt=cutoff,
        status=OTPVerification.EXPIRED
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} expired OTP records")
    return deleted_count


def make_user_admin(user):
    """
    Make a user an admin (superuser and staff).
    
    Args:
        user: Django User object
    
    Returns:
        Updated user object
    """
    user.is_staff = True
    user.is_superuser = True
    user.save()
    
    # Update profile role to admin if exists
    from .models import Profile, UserRole
    try:
        profile = Profile.objects.get(user=user)
        profile.role = UserRole.ADMIN
        profile.save()
    except Profile.DoesNotExist:
        pass
    
    logger.info(f"User {user.username} has been promoted to admin")
    return user
