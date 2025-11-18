from __future__ import annotations

import re
import secrets
from urllib.parse import urlencode

import requests
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from acham.users.api.serializers import EmailPhoneTokenObtainPairSerializer
from acham.users.api.serializers import EmailRegistrationSerializer
from acham.users.api.serializers import PhoneOTPLoginRequestSerializer
from acham.users.api.serializers import PhoneOTPVerifySerializer
from acham.users.api.serializers import PhoneRegistrationConfirmSerializer
from acham.users.api.serializers import PasswordChangeSerializer
from acham.users.api.serializers import UserSerializer


class AuthResponseMixin:
    """Utility mixin to assemble standardized auth responses."""

    @staticmethod
    def build_token_response(user, request, status_code=status.HTTP_200_OK) -> Response:
        refresh = RefreshToken.for_user(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user, context={"request": request}).data,
        }
        return Response(data, status=status_code)


class EmailRegistrationView(AuthResponseMixin, APIView):
    permission_classes = [AllowAny]
    serializer_class = EmailRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return self.build_token_response(user=user, request=request, status_code=status.HTTP_201_CREATED)


class PhoneOTPLoginRequestView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PhoneOTPLoginRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(
            {
                "detail": _("OTP sent to phone number."),
                "is_new_user": result.get("is_new_user", False),
            },
            status=status.HTTP_200_OK,
        )


class PhoneOTPVerifyView(AuthResponseMixin, APIView):
    permission_classes = [AllowAny]
    serializer_class = PhoneOTPVerifySerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return self.build_token_response(user=user, request=request, status_code=status.HTTP_200_OK)


class EmailPhoneTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = EmailPhoneTokenObtainPairSerializer


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": _("Password updated successfully.")}, status=status.HTTP_200_OK)


class SocialOAuthBaseView(AuthResponseMixin, APIView):
    permission_classes = [AllowAny]
    provider: str
    authorization_base_url: str
    token_url: str
    userinfo_url: str

    def get_scopes(self) -> list[str]:
        raise NotImplementedError

    def get_client_credentials(self) -> tuple[str, str]:
        raise NotImplementedError

    def build_authorization_url(self, redirect_uri: str, state: str) -> str:
        raise NotImplementedError

    @staticmethod
    def _state_cache_key(provider: str, state: str) -> str:
        return f"oauth:{provider}:state:{state}"

    def _store_state(self, state: str, payload: dict[str, str]) -> None:
        cache.set(self._state_cache_key(self.provider, state), payload, timeout=300)

    def _pop_state(self, state: str) -> dict[str, str] | None:
        key = self._state_cache_key(self.provider, state)
        payload = cache.get(key)
        if payload:
            cache.delete(key)
        return payload

    def _create_or_update_user(self, *, uid: str, email: str | None, name: str | None, extra_data: dict) -> tuple:
        from django.contrib.auth import get_user_model

        User = get_user_model()

        with transaction.atomic():
            email_lower = email.lower() if email else None
            generated_email = False
            if not email_lower:
                base = re.sub(r"[^a-z0-9]+", "-", f"{self.provider}-{uid}".lower()).strip("-") or f"{self.provider}-user"
                domain = f"{self.provider}.oauth.local"
                candidate = f"{base}@{domain}"
                suffix = 1
                while User.objects.filter(email__iexact=candidate).exists():
                    candidate = f"{base}-{suffix}@{domain}"
                    suffix += 1
                email_lower = candidate
                generated_email = True

            social_account = (
                SocialAccount.objects.select_related("user")
                .filter(provider=self.provider, uid=uid)
                .first()
            )
            if social_account:
                user = social_account.user
                social_account.extra_data = extra_data
                social_account.save(update_fields=["extra_data"])
            else:
                user = None
                if email_lower:
                    user = User.objects.filter(email__iexact=email_lower).first()
                if user is None:
                    user = User.objects.create_user(email=email_lower, password=None, name=name or "")
                else:
                    if name and not user.name:
                        user.name = name
                        user.save(update_fields=["name"])
                social_account = SocialAccount.objects.create(
                    provider=self.provider,
                    uid=uid,
                    user=user,
                    extra_data=extra_data,
                )
                if email_lower and not generated_email:
                    EmailAddress.objects.update_or_create(
                        user=user,
                        email=email_lower,
                        defaults={"verified": True, "primary": True},
                    )

        return user, social_account


class SocialOAuthAuthorizeView(SocialOAuthBaseView):
    def get(self, request, *args, **kwargs):
        redirect_uri = request.query_params.get("redirect_uri")
        if not redirect_uri:
            return Response({"detail": _("redirect_uri is required.")}, status=status.HTTP_400_BAD_REQUEST)

        client_id, _ = self.get_client_credentials()
        if not client_id:
            return Response({"detail": _("OAuth client_id is not configured.")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        state = secrets.token_urlsafe(32)
        self._store_state(state, {"redirect_uri": redirect_uri})
        authorization_url = self.build_authorization_url(redirect_uri=redirect_uri, state=state)
        return Response({"authorization_url": authorization_url, "state": state}, status=status.HTTP_200_OK)


class SocialOAuthCallbackView(SocialOAuthBaseView):
    def post(self, request, *args, **kwargs):
        code = request.data.get("code")
        state = request.data.get("state")
        redirect_uri = request.data.get("redirect_uri")

        if not code or not state or not redirect_uri:
            return Response({"detail": _("code, state, and redirect_uri are required.")}, status=status.HTTP_400_BAD_REQUEST)

        state_payload = self._pop_state(state)
        if not state_payload:
            return Response({"detail": _("Invalid or expired state parameter.")}, status=status.HTTP_400_BAD_REQUEST)

        if state_payload.get("redirect_uri") != redirect_uri:
            return Response({"detail": _("redirect_uri mismatch.")}, status=status.HTTP_400_BAD_REQUEST)

        client_id, client_secret = self.get_client_credentials()
        if not client_id or not client_secret:
            return Response({"detail": _("OAuth credentials are not configured.")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            tokens = self.exchange_code_for_token(
                code=code,
                redirect_uri=redirect_uri,
                client_id=client_id,
                client_secret=client_secret,
            )
            profile = self.fetch_user_profile(tokens=tokens, access_token=tokens.get("access_token"))
        except requests.RequestException as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        uid = profile.get("id") or profile.get("sub")
        if not uid:
            return Response({"detail": _("Unable to determine user identifier from provider response.")}, status=status.HTTP_400_BAD_REQUEST)

        email = profile.get("email")
        name = profile.get("name") or profile.get("given_name")

        user, _ = self._create_or_update_user(
            uid=str(uid),
            email=email,
            name=name,
            extra_data=profile,
        )
        return self.build_token_response(user=user, request=request, status_code=status.HTTP_200_OK)

    def exchange_code_for_token(self, *, code: str, redirect_uri: str, client_id: str, client_secret: str) -> dict:
        raise NotImplementedError

    def fetch_user_profile(self, *, tokens: dict, access_token: str | None) -> dict:
        raise NotImplementedError


class GoogleOAuthAuthorizeView(SocialOAuthAuthorizeView):
    provider = "google"
    authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    def get_scopes(self) -> list[str]:
        return settings.GOOGLE_OAUTH_SCOPES

    def get_client_credentials(self) -> tuple[str, str]:
        return settings.GOOGLE_OAUTH_CLIENT_ID, settings.GOOGLE_OAUTH_CLIENT_SECRET

    def build_authorization_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.get_client_credentials()[0],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.get_scopes()),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self.authorization_base_url}?{urlencode(params)}"


class GoogleOAuthCallbackView(SocialOAuthCallbackView, GoogleOAuthAuthorizeView):
    def exchange_code_for_token(self, *, code: str, redirect_uri: str, client_id: str, client_secret: str) -> dict:
        response = requests.post(
            self.token_url,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def fetch_user_profile(self, *, tokens: dict, access_token: str | None) -> dict:
        if not access_token:
            raise requests.RequestException("Access token not returned by Google.")
        response = requests.get(
            self.userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if "sub" in data and "id" not in data:
            data["id"] = data["sub"]
        return data


class FacebookOAuthAuthorizeView(SocialOAuthAuthorizeView):
    provider = "facebook"
    authorization_base_url = "https://www.facebook.com/v18.0/dialog/oauth"
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    userinfo_url = "https://graph.facebook.com/me"

    def get_scopes(self) -> list[str]:
        return settings.FACEBOOK_OAUTH_SCOPES

    def get_client_credentials(self) -> tuple[str, str]:
        return settings.FACEBOOK_OAUTH_CLIENT_ID, settings.FACEBOOK_OAUTH_CLIENT_SECRET

    def build_authorization_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.get_client_credentials()[0],
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
            "scope": ",".join(self.get_scopes()),
        }
        return f"{self.authorization_base_url}?{urlencode(params)}"


class FacebookOAuthCallbackView(SocialOAuthCallbackView, FacebookOAuthAuthorizeView):
    def exchange_code_for_token(self, *, code: str, redirect_uri: str, client_id: str, client_secret: str) -> dict:
        response = requests.get(
            self.token_url,
            params={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def fetch_user_profile(self, *, tokens: dict, access_token: str | None) -> dict:
        token = access_token or tokens.get("access_token")
        if not token:
            raise requests.RequestException("Access token not returned by Facebook.")
        response = requests.get(
            self.userinfo_url,
            params={"access_token": token, "fields": "id,name,email"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

