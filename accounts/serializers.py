from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Profile, UserRole, OTPVerification
from donations.models import DonorDetails

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["role", "phone_e164", "city", "area", "is_verified"]


class UserMeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "profile"]


class InitiateRegistrationSerializer(serializers.Serializer):
    """
    First step: User provides contact info and receives OTP.
    """
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_e164 = serializers.CharField(required=False, allow_blank=True, max_length=20)
    role = serializers.ChoiceField(choices=UserRole.choices)

    def validate(self, attrs):
        if not attrs.get("email") and not attrs.get("phone_e164"):
            raise serializers.ValidationError(
                "Either email or phone_e164 must be provided for OTP verification."
            )
        
        # Check if username already exists
        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})
        
        return attrs


class VerifyOTPAndCompleteRegistrationSerializer(serializers.Serializer):
    """
    Second step: User verifies OTP and completes registration with password.
    """
    username = serializers.CharField(max_length=150)
    otp_code = serializers.CharField(max_length=6, min_length=6)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_e164 = serializers.CharField(required=False, allow_blank=True, max_length=20)
    role = serializers.ChoiceField(choices=UserRole.choices)

    # Profile
    city = serializers.CharField(required=False, allow_blank=True, max_length=64)
    area = serializers.CharField(required=False, allow_blank=True, max_length=64)

    # Donor details
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=120)
    age = serializers.IntegerField(required=False, min_value=18, max_value=80)
    blood_group = serializers.CharField(required=False, allow_blank=True, max_length=3)

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate(self, attrs):
        # Verify OTP first
        from .services import verify_otp
        phone = attrs.get("phone_e164", "")
        email = attrs.get("email", "")
        otp_code = attrs.get("otp_code", "")

        is_valid, message = verify_otp(
            phone_e164=phone if phone else "",
            email=email if email else "",
            provided_otp=otp_code
        )
        
        if not is_valid:
            raise serializers.ValidationError({"otp_code": message})

        # Then validate donor fields AFTER OTP verified
        role = attrs.get("role")
        if role == UserRole.DONOR:
            for f in ["full_name", "age", "blood_group", "city"]:
                if not attrs.get(f):
                    raise serializers.ValidationError({f: "Required for donor registration."})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        username = validated_data.pop("username")
        otp_code = validated_data.pop("otp_code")
        role = validated_data.pop("role", UserRole.PATIENT)

        phone_e164 = validated_data.pop("phone_e164", "")
        email = validated_data.pop("email", "")
        city = validated_data.pop("city", "")
        area = validated_data.pop("area", "")

        full_name = validated_data.pop("full_name", "")
        age = validated_data.pop("age", None)
        blood_group = validated_data.pop("blood_group", "")

        # Create user with email
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        user.save()

        # Update profile with verification
        user.profile.role = role
        user.profile.phone_e164 = phone_e164
        user.profile.city = city
        user.profile.area = area
        user.profile.is_verified = True  # Mark as verified after OTP confirmation
        user.profile.save()

        # Create donor details if role is donor
        if role == UserRole.DONOR:
            DonorDetails.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": full_name,
                    "age": age,
                    "blood_group": blood_group,
                    "city": city,
                    "area": area,
                },
            )

        return user


class RegisterSerializer(serializers.Serializer):
    """
    Legacy: One-step registration (kept for backward compatibility).
    New users should use InitiateRegistration + VerifyOTPAndCompleteRegistration.
    """
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserRole.choices)

    # Profile
    phone_e164 = serializers.CharField(required=False, allow_blank=True, max_length=20)
    city = serializers.CharField(required=False, allow_blank=True, max_length=64)
    area = serializers.CharField(required=False, allow_blank=True, max_length=64)

    # Donor details
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=120)
    age = serializers.IntegerField(required=False, min_value=18, max_value=80)
    blood_group = serializers.CharField(required=False, allow_blank=True, max_length=3)

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate(self, attrs):
        role = attrs.get("role")
        if role == UserRole.DONOR:
            for f in ["full_name", "age", "blood_group", "city"]:
                if not attrs.get(f):
                    raise serializers.ValidationError({f: "Required for donor registration."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.pop("role")

        phone_e164 = validated_data.pop("phone_e164", "")
        city = validated_data.pop("city", "")
        area = validated_data.pop("area", "")

        full_name = validated_data.pop("full_name", "")
        age = validated_data.pop("age", None)
        blood_group = validated_data.pop("blood_group", "")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=password,
        )
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        user.save()
        user.profile.role = role
        user.profile.phone_e164 = phone_e164
        user.profile.city = city
        user.profile.area = area
        user.profile.save()

        if role == UserRole.DONOR:
            DonorDetails.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": full_name,
                    "age": age,
                    "blood_group": blood_group,
                    "city": city,
                    "area": area,
                },
            )

        return user


