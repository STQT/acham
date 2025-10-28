from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    CountryListView,
    UserRegistrationView,
    OTPVerificationView,
    ResendOTPView
)

router = DefaultRouter()
router.register("users", UserViewSet)

app_name = "users"
urlpatterns = [
    # Country endpoints
    path("countries/", CountryListView.as_view(), name="country-list"),
    
    # Registration endpoints
    path("register/", UserRegistrationView.as_view(), name="user-registration"),
    
    # OTP endpoints
    path("verify-otp/<int:user_id>/", OTPVerificationView.as_view(), name="otp-verification"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    
    # Include router URLs
    *router.urls,
]
