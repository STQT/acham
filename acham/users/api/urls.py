from django.urls import path
from .views import (
    CountryListView,
    UserRegistrationView,
    OTPVerificationView,
    ResendOTPView,
    ProfileMeViewSet,
    ChangePasswordView,
    JwtLogoutView
)

app_name = "users"
urlpatterns = [
    # ----- ONLY expose these endpoints, no user listing/detail endpoints! -----
    path("countries/", CountryListView.as_view(), name="country-list"),
    path("register/", UserRegistrationView.as_view(), name="user-registration"),
    path("verify-otp/<int:user_id>/", OTPVerificationView.as_view(), name="otp-verification"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("me/", ProfileMeViewSet.as_view(), name="profile-me"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("logout/", JwtLogoutView.as_view(), name="logout"),
]
# No DRF router - API is tight, secure, and product-oriented!
