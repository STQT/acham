"""Service for generating and sending admin OTP codes via Telegram."""

from __future__ import annotations

import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from acham.orders.services.telegram_service import TelegramBotClient, TelegramConfigurationError, TelegramAPIError
from acham.users.models import AdminOTP, User

logger = logging.getLogger(__name__)


class AdminOTPService:
    """Service for managing admin OTP codes."""

    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10
    MAX_ATTEMPTS = 5

    @classmethod
    def generate_otp(cls) -> str:
        """Generate a random 6-digit OTP code."""
        return f"{secrets.randbelow(1000000):06d}"

    @classmethod
    def create_otp(
        cls,
        user: User,
        session_key: str,
        ip_address: str | None = None,
        user_agent: str = "",
    ) -> AdminOTP:
        """Create a new OTP code for admin login.
        
        Args:
            user: User attempting to login
            session_key: Django session key
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            AdminOTP instance
        """
        # Deactivate any existing active OTPs for this session
        AdminOTP.objects.filter(
            session_key=session_key,
            is_active=True,
            verified_at__isnull=True,
        ).update(is_active=False)

        # Generate new OTP
        code = cls.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=cls.OTP_EXPIRY_MINUTES)

        otp = AdminOTP.objects.create(
            user=user,
            code=code,
            session_key=session_key,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Send OTP via Telegram
        try:
            cls.send_otp_via_telegram(user, code)
        except Exception as exc:
            logger.error(f"Failed to send OTP via Telegram: {exc}", exc_info=True)
            # Don't fail the OTP creation if Telegram fails, but log it

        return otp

    @classmethod
    def send_otp_via_telegram(cls, user: User, code: str) -> None:
        """Send OTP code to Telegram group.
        
        Args:
            user: User attempting to login
            code: OTP code to send
        """
        try:
            telegram_client = TelegramBotClient()
            
            user_info = []
            user_info.append(f"👤 Пользователь: {user.name or user.email or 'Unknown'}")
            user_info.append(f"📧 Email: {user.email or 'Не указан'}")
            if user.phone:
                user_info.append(f"📱 Телефон: {user.phone}")
            
            message = f"""
🔐 <b>Код для входа в админку</b>

{chr(10).join(user_info)}

🔑 <b>Код: {code}</b>

⏰ Код действителен {cls.OTP_EXPIRY_MINUTES} минут
            """.strip()

            telegram_client.send_message(message)
            logger.info(f"OTP code sent to Telegram for user {user.email}")
            
        except TelegramConfigurationError:
            logger.warning("Telegram bot not configured, skipping OTP notification")
        except TelegramAPIError as exc:
            logger.error(f"Telegram API error when sending OTP: {exc}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error sending OTP via Telegram: {exc}", exc_info=True)
            raise

    @classmethod
    def verify_otp(cls, session_key: str, code: str) -> AdminOTP | None:
        """Verify OTP code for admin login.
        
        Args:
            session_key: Django session key
            code: OTP code to verify
            
        Returns:
            AdminOTP instance if valid, None otherwise
        """
        try:
            otp = AdminOTP.objects.get(
                session_key=session_key,
                code=code,
                is_active=True,
                verified_at__isnull=True,
            )
        except AdminOTP.DoesNotExist:
            return None

        # Check if expired
        if otp.is_expired():
            otp.is_active = False
            otp.save(update_fields=["is_active"])
            return None

        # Check attempts
        if otp.attempts >= cls.MAX_ATTEMPTS:
            otp.is_active = False
            otp.save(update_fields=["is_active"])
            return None

        # Increment attempts
        otp.attempts += 1
        otp.save(update_fields=["attempts"])

        # Verify code
        if otp.code == code:
            otp.verified_at = timezone.now()
            otp.is_active = False
            otp.save(update_fields=["verified_at", "is_active"])
            return otp

        return None

    @classmethod
    def cleanup_expired_otps(cls) -> int:
        """Clean up expired OTP codes.
        
        Returns:
            Number of OTPs deactivated
        """
        count = AdminOTP.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True,
        ).update(is_active=False)
        
        logger.info(f"Cleaned up {count} expired admin OTP codes")
        return count
