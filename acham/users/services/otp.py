"""OTP utilities for phone verification and login."""

from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Tuple

from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from acham.users.models import PhoneOTP

from .eskiz import EskizAPIError
from .eskiz import EskizConfigurationError
from .eskiz import EskizSMSClient

DEFAULT_OTP_TTL = timedelta(minutes=5)
MAX_ATTEMPTS = 5


class OTPError(RuntimeError):
    """Raised when OTP validation fails."""


def generate_otp_code(length: int = 6) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length))


def create_phone_otp(
    phone: str,
    purpose: str,
    ttl: timedelta = DEFAULT_OTP_TTL,
) -> Tuple[PhoneOTP, str]:
    code = generate_otp_code()
    expires_at = timezone.now() + ttl

    with transaction.atomic():
        PhoneOTP.objects.filter(phone=phone, purpose=purpose, is_active=True).update(is_active=False)
        otp = PhoneOTP.objects.create(
            phone=phone,
            purpose=purpose,
            code_hash=make_password(code),
            expires_at=expires_at,
        )
    return otp, code


def send_phone_otp(phone: str, purpose: str, template: str | None = None) -> str:
    otp, code = create_phone_otp(phone=phone, purpose=purpose)

    if template:
        message = template.format(code=code)
    else:
        message = _("Confirmation code for registration on the Acham.uz website: {code}").format(code=code)

    try:
        client = EskizSMSClient()
        client.send_sms(phone=phone, message=message)
    except (EskizConfigurationError, EskizAPIError) as exc:  # noqa: PERF203
        raise OTPError(str(exc)) from exc

    return code


def verify_phone_otp(phone: str, purpose: str, code: str) -> PhoneOTP:
    otp = (
        PhoneOTP.objects.filter(
            phone=phone,
            purpose=purpose,
            is_active=True,
        )
        .order_by("-created_at")
        .first()
    )

    if otp is None:
        raise OTPError(_("OTP code not found or expired."))

    if otp.expires_at < timezone.now():
        otp.is_active = False
        otp.save(update_fields=["is_active"])
        raise OTPError(_("OTP code expired."))

    if not check_password(code, otp.code_hash):
        otp.attempts += 1
        if otp.attempts >= MAX_ATTEMPTS:
            otp.is_active = False
        otp.save(update_fields=["attempts", "is_active"])
        raise OTPError(_("Invalid OTP code."))

    otp.is_active = False
    otp.verified_at = timezone.now()
    otp.save(update_fields=["is_active", "verified_at"])
    return otp

