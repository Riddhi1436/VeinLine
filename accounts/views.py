from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    RegisterSerializer, 
    UserMeSerializer,
    InitiateRegistrationSerializer,
    VerifyOTPAndCompleteRegistrationSerializer
)
from .services import send_otp, make_user_admin

from django.shortcuts import render
from django.contrib.auth.models import User


class RegisterView(generics.CreateAPIView):
    """Legacy one-step registration endpoint (kept for backward compatibility)."""
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class InitiateRegistrationView(APIView):
    """
    Step 1: User provides username, role, and contact (email/phone).
    Returns OTP to be verified in next step.
    
    POST /api/auth/register/initiate/
    {
        "username": "john_doe",
        "email": "john@example.com",
        "phone_e164": "+911234567890",
        "role": "patient"
    }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = InitiateRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        email = serializer.validated_data.get("email", "")
        phone_e164 = serializer.validated_data.get("phone_e164", "")
        role = serializer.validated_data["role"]

        # Send OTP
        try:
            otp_result = send_otp(phone_e164=phone_e164, email=email)
            
            return Response(
                {
                    "status": "success",
                    "message": f"OTP sent to {phone_e164 or email}. Valid for 10 minutes.",
                    "otp_id": otp_result["otp_id"],
                    "contact": otp_result["contact"],
                    "next_step": "Verify OTP and complete registration at /api/auth/register/verify-otp/",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "message": f"Failed to send OTP: {str(e)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class VerifyOTPAndCompleteRegistrationView(APIView):
    """
    Step 2: User verifies OTP and completes registration with password and profile info.
    
    POST /api/auth/register/verify-otp/
    {
        "username": "john_doe",
        "email": "john@example.com",
        "phone_e164": "+911234567890",
        "otp_code": "123456",
        "password": "secure_password_here",
        "role": "patient",
        "city": "Delhi",
        "area": "Central Delhi"
    }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPAndCompleteRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        
        # Make first user an admin automatically
        if User.objects.count() == 1:
            make_user_admin(user)
            is_admin = True
        else:
            is_admin = False

        return Response(
            {
                "status": "success",
                "message": f"Registration completed successfully. Welcome {user.username}!" + (" You are now an admin!" if is_admin else ""),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.profile.role,
                    "is_verified": user.profile.is_verified,
                    "is_admin": is_admin,
                },
                "next_step": "Login using JWT token at /api/auth/token/",
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveAPIView):
    serializer_class = UserMeSerializer

    def get(self, request, *args, **kwargs):
        return Response(UserMeSerializer(request.user).data)

