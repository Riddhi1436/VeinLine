from django.urls import path

from .views import (
    MeView, 
    RegisterView,
    InitiateRegistrationView,
    VerifyOTPAndCompleteRegistrationView
)

urlpatterns = [
    # Legacy one-step registration (backward compatibility)
    path("auth/register/", RegisterView.as_view(), name="register"),
    
    # OTP-based two-step registration (new secure flow)
    path("auth/register/initiate/", InitiateRegistrationView.as_view(), name="initiate_registration"),
    path("auth/register/verify-otp/", VerifyOTPAndCompleteRegistrationView.as_view(), name="verify_otp_registration"),
    
    # User profile
    path("auth/me/", MeView.as_view(), name="me"),
]


