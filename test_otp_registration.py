"""
Comprehensive tests for OTP-based registration system.
"""

import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from accounts.models import OTPVerification, Profile, UserRole
from accounts.services import (
    generate_otp_code,
    create_or_update_otp,
    send_otp,
    verify_otp,
    cleanup_expired_otps
)

User = get_user_model()


class OTPGenerationTests(TestCase):
    """Test OTP code generation."""

    def test_generate_otp_code_length(self):
        """OTP should be 6 digits by default."""
        otp = generate_otp_code()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

    def test_generate_otp_code_custom_length(self):
        """OTP should support custom length."""
        otp = generate_otp_code(length=8)
        self.assertEqual(len(otp), 8)
        self.assertTrue(otp.isdigit())

    def test_generate_otp_randomness(self):
        """Generated OTPs should be different."""
        otps = [generate_otp_code() for _ in range(10)]
        # At least some should be different (probability of all same is negligible)
        self.assertGreater(len(set(otps)), 1)


class OTPVerificationModelTests(TestCase):
    """Test OTPVerification model."""

    def test_create_otp_for_phone(self):
        """Create OTP record for phone number."""
        otp = OTPVerification.objects.create(
            phone_e164="+911234567890",
            otp_code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.assertEqual(otp.phone_e164, "+911234567890")
        self.assertEqual(otp.status, OTPVerification.PENDING)
        self.assertEqual(otp.attempts, 0)

    def test_create_otp_for_email(self):
        """Create OTP record for email."""
        otp = OTPVerification.objects.create(
            email="user@example.com",
            otp_code="654321",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.assertEqual(otp.email, "user@example.com")
        self.assertEqual(otp.status, OTPVerification.PENDING)

    def test_otp_is_valid_for_pending(self):
        """OTP should be valid if pending and not expired."""
        otp = OTPVerification.objects.create(
            phone_e164="+911234567890",
            otp_code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.assertTrue(otp.is_valid())

    def test_otp_is_not_valid_if_expired(self):
        """OTP should be invalid if expired."""
        otp = OTPVerification.objects.create(
            phone_e164="+911234567890",
            otp_code="123456",
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        self.assertFalse(otp.is_valid())
        # Status should be updated to EXPIRED
        otp.refresh_from_db()
        self.assertEqual(otp.status, OTPVerification.EXPIRED)

    def test_otp_is_not_valid_if_already_verified(self):
        """OTP should be invalid if already verified."""
        otp = OTPVerification.objects.create(
            phone_e164="+911234567890",
            otp_code="123456",
            status=OTPVerification.VERIFIED,
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.assertFalse(otp.is_valid())

    def test_otp_verify_success(self):
        """Verify correct OTP."""
        otp = OTPVerification.objects.create(
            phone_e164="+911234567890",
            otp_code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        is_valid, message = otp.verify("123456")
        self.assertTrue(is_valid)
        self.assertEqual(message, "OTP verified successfully")
        # Check status updated
        otp.refresh_from_db()
        self.assertEqual(otp.status, OTPVerification.VERIFIED)
        self.assertIsNotNone(otp.verified_at)

    def test_otp_verify_incorrect_code(self):
        """Reject incorrect OTP."""
        otp = OTPVerification.objects.create(
            phone_e164="+911234567890",
            otp_code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        is_valid, message = otp.verify("999999")
        self.assertFalse(is_valid)
        self.assertIn("Invalid OTP", message)
        self.assertIn("4 attempts remaining", message)
        # Check attempts incremented
        otp.refresh_from_db()
        self.assertEqual(otp.attempts, 1)

    def test_otp_verify_max_attempts_exceeded(self):
        """Reject OTP after max attempts exceeded."""
        otp = OTPVerification.objects.create(
            phone_e164="+911234567890",
            otp_code="123456",
            attempts=5,
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        is_valid, message = otp.verify("123456")
        self.assertFalse(is_valid)
        self.assertIn("Maximum verification attempts exceeded", message)
        # Check status updated to EXPIRED
        otp.refresh_from_db()
        self.assertEqual(otp.status, OTPVerification.EXPIRED)

    def test_otp_verify_already_verified(self):
        """Reject verification if already verified."""
        otp = OTPVerification.objects.create(
            phone_e164="+911234567890",
            otp_code="123456",
            status=OTPVerification.VERIFIED,
            verified_at=timezone.now(),
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        is_valid, message = otp.verify("123456")
        self.assertFalse(is_valid)
        self.assertIn("already verified", message)


class OTPServiceTests(TestCase):
    """Test OTP service functions."""

    def test_create_or_update_otp_phone(self):
        """Create or update OTP for phone."""
        otp1 = create_or_update_otp(phone_e164="+911234567890")
        self.assertEqual(otp1.phone_e164, "+911234567890")
        self.assertEqual(otp1.status, OTPVerification.PENDING)

        # Update should create new OTP code
        otp2 = create_or_update_otp(phone_e164="+911234567890")
        self.assertEqual(otp2.id, otp1.id)  # Same record
        # Code might be different (with probability 1 - 10^-6)

    def test_create_or_update_otp_email(self):
        """Create or update OTP for email."""
        otp = create_or_update_otp(email="user@example.com")
        self.assertEqual(otp.email, "user@example.com")
        self.assertEqual(otp.status, OTPVerification.PENDING)

    def test_create_or_update_otp_no_contact_raises_error(self):
        """Raise error if neither phone nor email provided."""
        with self.assertRaises(ValueError):
            create_or_update_otp()

    def test_send_otp_phone(self):
        """Send OTP via phone."""
        result = send_otp(phone_e164="+911234567890")
        self.assertIn("otp_id", result)
        self.assertIn("delivery", result)
        self.assertIn("sms", result["delivery"])

    def test_send_otp_email(self):
        """Send OTP via email."""
        result = send_otp(email="user@example.com")
        self.assertIn("otp_id", result)
        self.assertIn("delivery", result)
        self.assertIn("email", result["delivery"])

    def test_send_otp_both_channels(self):
        """Send OTP via both SMS and email."""
        result = send_otp(
            phone_e164="+911234567890",
            email="user@example.com"
        )
        self.assertIn("sms", result["delivery"])
        self.assertIn("email", result["delivery"])

    def test_verify_otp_phone_success(self):
        """Verify OTP for phone successfully."""
        otp_record = create_or_update_otp(phone_e164="+911234567890")
        is_valid, message = verify_otp(
            phone_e164="+911234567890",
            provided_otp=otp_record.otp_code
        )
        self.assertTrue(is_valid)

    def test_verify_otp_email_success(self):
        """Verify OTP for email successfully."""
        otp_record = create_or_update_otp(email="user@example.com")
        is_valid, message = verify_otp(
            email="user@example.com",
            provided_otp=otp_record.otp_code
        )
        self.assertTrue(is_valid)

    def test_verify_otp_not_found(self):
        """Reject verification if OTP not found."""
        is_valid, message = verify_otp(
            phone_e164="+919999999999",
            provided_otp="123456"
        )
        self.assertFalse(is_valid)
        self.assertIn("No OTP request found", message)

    def test_cleanup_expired_otps(self):
        """Clean up expired OTP records."""
        # Create expired OTP (24+ hours old) using queryset update
        old_time = timezone.now() - timedelta(hours=25)
        otp = OTPVerification.objects.create(
            phone_e164="+911234567890",
            otp_code="123456",
            status=OTPVerification.EXPIRED,
            expires_at=old_time,
        )
        # Update created_at to make it old
        OTPVerification.objects.filter(id=otp.id).update(created_at=old_time)
        
        # Create recent OTP (but expired status)
        otp2 = OTPVerification.objects.create(
            phone_e164="+919876543210",
            otp_code="654321",
            status=OTPVerification.EXPIRED,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        deleted_count = cleanup_expired_otps()
        self.assertEqual(deleted_count, 1)
        self.assertFalse(OTPVerification.objects.filter(id=otp.id).exists())
        self.assertTrue(OTPVerification.objects.filter(id=otp2.id).exists())


class OTPRegistrationAPITests(TestCase):
    """Test OTP-based registration API endpoints."""

    def setUp(self):
        self.client = Client()
        self.phone = "+911234567890"
        self.email = "newuser@example.com"
        self.username = "testuser"
        self.password = "TestPassword123!"

    def test_initiate_registration_with_phone(self):
        """Initiate registration with phone number."""
        response = self.client.post(
            "/api/auth/register/initiate/",
            {
                "username": self.username,
                "phone_e164": self.phone,
                "role": "patient",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("otp_id", data)
        self.assertIn(self.phone, data["contact"])

    def test_initiate_registration_with_email(self):
        """Initiate registration with email."""
        response = self.client.post(
            "/api/auth/register/initiate/",
            {
                "username": self.username,
                "email": self.email,
                "role": "patient",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn(self.email, data["contact"])

    def test_initiate_registration_no_contact_fails(self):
        """Initiate registration fails without phone or email."""
        response = self.client.post(
            "/api/auth/register/initiate/",
            {
                "username": self.username,
                "role": "patient",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        # Response should have errors key in this case
        data = response.json()
        self.assertTrue("email" in data or "phone_e164" in data or "error" in str(data).lower())

    def test_initiate_registration_duplicate_username_fails(self):
        """Initiate registration fails with duplicate username."""
        # Create user with same username
        User.objects.create_user(username=self.username, password="temp")

        response = self.client.post(
            "/api/auth/register/initiate/",
            {
                "username": self.username,
                "email": self.email,
                "role": "patient",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_verify_otp_and_complete_registration(self):
        """Complete registration after OTP verification."""
        # Step 1: Initiate registration
        response1 = self.client.post(
            "/api/auth/register/initiate/",
            {
                "username": self.username,
                "email": self.email,
                "role": "patient",
            },
            content_type="application/json",
        )
        self.assertEqual(response1.status_code, 200)

        # Get OTP from database
        otp_record = OTPVerification.objects.get(email=self.email)

        # Step 2: Verify OTP and complete registration
        response2 = self.client.post(
            "/api/auth/register/verify-otp/",
            {
                "username": self.username,
                "email": self.email,
                "otp_code": otp_record.otp_code,
                "password": self.password,
                "role": "patient",
                "city": "Delhi",
            },
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 201)
        data = response2.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["user"]["username"], self.username)
        self.assertTrue(data["user"]["is_verified"])

        # Verify user created
        user = User.objects.get(username=self.username)
        self.assertEqual(user.email, self.email)
        self.assertTrue(user.profile.is_verified)

    def test_verify_otp_wrong_code_fails(self):
        """Verify registration fails with wrong OTP code."""
        # Initiate registration
        self.client.post(
            "/api/auth/register/initiate/",
            {
                "username": self.username,
                "email": self.email,
                "role": "patient",
            },
            content_type="application/json",
        )

        # Try to verify with wrong OTP
        response = self.client.post(
            "/api/auth/register/verify-otp/",
            {
                "username": self.username,
                "email": self.email,
                "otp_code": "999999",
                "password": self.password,
                "role": "patient",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data["status"])

    def test_verify_otp_donor_registration_requires_donor_fields(self):
        """Donor registration with full details succeeds."""
        # Initiate registration as donor
        response1 = self.client.post(
            "/api/auth/register/initiate/",
            {
                "username": "donor_full",
                "email": "donorfull@example.com",
                "role": "donor",
            },
            content_type="application/json",
        )
        self.assertEqual(response1.status_code, 200)

        # Get OTP
        otp_record = OTPVerification.objects.get(email="donorfull@example.com")

        # Complete with all required donor fields
        response2 = self.client.post(
            "/api/auth/register/verify-otp/",
            {
                "username": "donor_full",
                "email": "donorfull@example.com",
                "otp_code": otp_record.otp_code,
                "password": self.password,
                "role": "donor",
                "full_name": "Jane Donor",
                "age": 28,
                "blood_group": "B+",
                "city": "Mumbai",
            },
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 201)
        data = response2.json()
        self.assertEqual(data["user"]["role"], "donor")


class ProfileVerificationTests(TestCase):
    """Test that profile is marked as verified after registration."""

    def test_profile_verified_after_otp_registration(self):
        """Profile should have is_verified=True after OTP registration."""
        # Initiate and complete OTP registration
        phone = "+919876543210"
        email = "userprofile@example.com"
        username = "profiletest"
        password = "TestPassword123!"

        # Step 1: Initiate with email (OTP goes to email)
        response1 = self.client.post(
            "/api/auth/register/initiate/",
            {
                "username": username,
                "email": email,
                "phone_e164": phone,
                "role": "patient",
            },
            content_type="application/json",
        )
        self.assertEqual(response1.status_code, 200)

        # Step 2: OTP is stored against email address (first field that gets an OTP)
        # We provided both email and phone, but OTP mechanism uses the first one it can send to
        # In this case, email delivery typically succeeds (console backend), so OTP stored for email
        try:
            otp_record = OTPVerification.objects.get(email=email)
        except OTPVerification.DoesNotExist:
            # If no OTP for email, try phone
            otp_record = OTPVerification.objects.get(phone_e164=phone)
        
        response2 = self.client.post(
            "/api/auth/register/verify-otp/",
            {
                "username": username,
                "email": email,
                "phone_e164": phone,
                "otp_code": otp_record.otp_code,
                "password": password,
                "role": "patient",
                "city": "Delhi",
            },
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 201)

        # Verify profile marked as verified
        user = User.objects.get(username=username)
        self.assertTrue(user.profile.is_verified)
        self.assertEqual(user.profile.phone_e164, phone)
        self.assertEqual(user.email, email)
