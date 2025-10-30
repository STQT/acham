from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    CountryListView,
    UserRegistrationView,
    OTPVerificationView,
    ResendOTPView,
    ProfileMeViewSet,
    ChangePasswordView,
    JwtLogoutView
)

router = DefaultRouter()
router.register("users", UserViewSet)

app_name = "users"
urlpatterns = [
    # Country endpoints
    path("countries/", CountryListView.as_view(), name="country-list"),
    
    # Registration/end-user endpoints
    path("register/", UserRegistrationView.as_view(), name="user-registration"),
    path("verify-otp/<int:user_id>/", OTPVerificationView.as_view(), name="otp-verification"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    # Profile
    path("me/", ProfileMeViewSet.as_view(), name="profile-me"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("logout/", JwtLogoutView.as_view(), name="logout"),
    # Include router URLs
    *router.urls,
]
