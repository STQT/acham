"""Eskiz SMS sending client."""

from __future__ import annotations

import logging
import re
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class EskizConfigurationError(RuntimeError):
    """Raised when Eskiz credentials are not configured."""


class EskizAPIError(RuntimeError):
    """Raised when Eskiz API returns an unexpected response."""


class EskizSMSClient:
    """Minimal Eskiz client for sending OTP codes."""

    AUTH_URL = "https://notify.eskiz.uz/api/auth/login"
    SMS_URL = "https://notify.eskiz.uz/api/message/sms/send"
    CACHE_KEY = "eskiz:api_token"

    def __init__(self) -> None:
        if not settings.ESKIZ_EMAIL or not settings.ESKIZ_PASSWORD:
            raise EskizConfigurationError("Eskiz credentials are not configured.")

        self._email = settings.ESKIZ_EMAIL
        self._password = settings.ESKIZ_PASSWORD
        if not settings.ESKIZ_SENDER:
            raise EskizConfigurationError("ESKIZ_SENDER environment variable is required.")

        self._sender = settings.ESKIZ_SENDER
        self._callback_url = settings.ESKIZ_CALLBACK_URL

    def _authenticate(self) -> str:
        response = requests.post(
            self.AUTH_URL,
            data={
                "email": self._email,
                "password": self._password,
            },
            timeout=10,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:  # noqa: TRY201
            msg = f"Eskiz auth failed: {response.text}"
            raise EskizAPIError(msg) from exc

        payload = response.json()
        token = payload.get("data", {}).get("token")
        if not token:
            msg = f"Eskiz auth response missing token: {payload}"
            raise EskizAPIError(msg)

        cache.set(self.CACHE_KEY, token, timeout=60 * 60 * 12)  # 12 hours
        return token

    def _get_token(self) -> str:
        token: str | None = cache.get(self.CACHE_KEY)
        if token:
            return token
        return self._authenticate()

    def send_sms(self, phone: str, message: str) -> dict[str, Any]:
        token = self._get_token()
        formatted_phone = self._format_phone(phone)

        response = requests.post(
            self.SMS_URL,
            headers={"Authorization": f"Bearer {token}"},
            data={
                "mobile_phone": formatted_phone,
                "message": message,
                "from": self._sender,
                "callback_url": self._callback_url,
            },
            timeout=10,
        )

        if response.status_code == 401:
            logger.info("Eskiz token expired, re-authenticating.")
            token = self._authenticate()
            response = requests.post(
                self.SMS_URL,
                headers={"Authorization": f"Bearer {token}"},
                data={
                    "mobile_phone": formatted_phone,
                    "message": message,
                    "from": self._sender,
                    "callback_url": self._callback_url,
                },
                timeout=10,
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:  # noqa: TRY201
            msg = f"Eskiz send failed: {response.text}"
            raise EskizAPIError(msg) from exc

        payload = response.json()
        logger.debug("Eskiz send response: %s", payload)
        return payload

    @staticmethod
    def _format_phone(phone: str) -> str:
        cleaned = re.sub(r"[^\d]", "", phone)
        if cleaned.startswith("998") and len(cleaned) == 12:
            return cleaned
        if cleaned.startswith("0") and len(cleaned) == 9:
            return f"998{cleaned[1:]}"
        if cleaned.startswith("9") and len(cleaned) == 9:
            return f"998{cleaned}"
        return cleaned

