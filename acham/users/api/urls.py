from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenVerifyView

from acham.users.api.auth_views import EmailPhoneTokenObtainPairView
from acham.users.api.auth_views import EmailRegistrationView
from acham.users.api.auth_views import FacebookOAuthAuthorizeView
from acham.users.api.auth_views import FacebookOAuthCallbackView
from acham.users.api.auth_views import GoogleOAuthAuthorizeView
from acham.users.api.auth_views import GoogleOAuthCallbackView
from acham.users.api.auth_views import PhoneOTPLoginRequestView
from acham.users.api.auth_views import PhoneOTPVerifyView
from acham.users.api.auth_views import PhoneRegistrationConfirmView
from acham.users.api.auth_views import PasswordChangeView

urlpatterns = [
    path("auth/register/email/", EmailRegistrationView.as_view(), name="auth-register-email"),
    path("auth/register/phone/confirm/", PhoneRegistrationConfirmView.as_view(), name="auth-register-phone-confirm"),
    path("auth/login/", EmailPhoneTokenObtainPairView.as_view(), name="auth-login"),
    path("auth/login/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/login/verify/", TokenVerifyView.as_view(), name="auth-verify"),
    path("auth/login/phone/request/", PhoneOTPLoginRequestView.as_view(), name="auth-login-phone-request"),
    path("auth/login/phone/verify/", PhoneOTPVerifyView.as_view(), name="auth-login-phone-verify"),
    path("auth/social/google/authorize/", GoogleOAuthAuthorizeView.as_view(), name="auth-google-authorize"),
    path("auth/social/google/callback/", GoogleOAuthCallbackView.as_view(), name="auth-google-callback"),
    path("auth/social/facebook/authorize/", FacebookOAuthAuthorizeView.as_view(), name="auth-facebook-authorize"),
    path("auth/social/facebook/callback/", FacebookOAuthCallbackView.as_view(), name="auth-facebook-callback"),
    path("auth/password/change/", PasswordChangeView.as_view(), name="auth-password-change"),
]

