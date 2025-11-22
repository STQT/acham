"""Service for interacting with OCTO payment gateway API."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class OctoService:
    """Service for OCTO payment gateway integration."""

    BASE_URL = getattr(settings, "OCTO_API_URL", "https://secure.octo.uz")
    SHOP_ID = getattr(settings, "OCTO_SHOP_ID", None)
    SECRET = getattr(settings, "OCTO_SECRET", None)
    TEST_MODE = getattr(settings, "OCTO_TEST_MODE", False)

    @classmethod
    def _make_request(
        cls,
        endpoint: str,
        payload: Dict[str, Any],
        method: str = "POST",
    ) -> Dict[str, Any]:
        """Make HTTP request to OCTO API."""
        url = f"{cls.BASE_URL}/{endpoint}"
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.request(
                method=method,
                url=url,
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"OCTO API request failed: {e}", exc_info=True)
            raise

    @classmethod
    def prepare_payment(
        cls,
        shop_transaction_id: str,
        total_sum: Decimal,
        user_data: Dict[str, str],
        basket: list[Dict[str, Any]],
        return_url: str,
        notify_url: str,
        language: str = "uz",
        payment_methods: Optional[list[Dict[str, str]]] = None,
        description: str = "",
        ttl: int = 15,
    ) -> Dict[str, Any]:
        """
        Prepare payment transaction.

        Args:
            shop_transaction_id: Unique transaction ID on our side
            total_sum: Total amount in UZS
            user_data: Dict with user_id, phone, email
            basket: List of basket items
            return_url: URL to redirect after payment
            notify_url: URL for payment notifications
            language: Language code (uz, ru, en)
            payment_methods: List of payment methods
            description: Payment description
            ttl: Time to live in minutes

        Returns:
            Response from OCTO API
        """
        if not cls.SHOP_ID or not cls.SECRET:
            raise ValueError("OCTO_SHOP_ID and OCTO_SECRET must be configured")

        if payment_methods is None:
            payment_methods = [
                {"method": "bank_card"},
                {"method": "uzcard"},
                {"method": "humo"},
            ]

        payload = {
            "octo_shop_id": cls.SHOP_ID,
            "octo_secret": cls.SECRET,
            "shop_transaction_id": shop_transaction_id,
            "auto_capture": True,  # One-stage payment
            "test": cls.TEST_MODE,
            "init_time": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_data": user_data,
            "total_sum": float(total_sum),
            "currency": "UZS",
            "description": description or f"Payment for order {shop_transaction_id}",
            "basket": basket,
            "payment_methods": payment_methods,
            "return_url": return_url,
            "notify_url": notify_url,
            "language": language,
            "ttl": ttl,
        }

        return cls._make_request("prepare_payment", payload)

    @classmethod
    def pay(
        cls,
        transaction_id: str,
        card_data: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Confirm payment with card data.

        Args:
            transaction_id: OCTO transaction ID from prepare_payment
            card_data: Dict with card_number, expire, cardholder_name

        Returns:
            Response from OCTO API
        """
        if not cls.SHOP_ID or not cls.SECRET:
            raise ValueError("OCTO_SHOP_ID and OCTO_SECRET must be configured")

        payload = {
            "octo_shop_id": cls.SHOP_ID,
            "octo_secret": cls.SECRET,
            "transaction_id": transaction_id,
            **card_data,
        }

        return cls._make_request("pay", payload)

    @classmethod
    def verification_info(cls, transaction_id: str) -> Dict[str, Any]:
        """
        Get verification information (payment ID and OTP form URL).

        Args:
            transaction_id: OCTO transaction ID from prepare_payment

        Returns:
            Response from OCTO API with payment_id and verification_url
        """
        if not cls.SHOP_ID or not cls.SECRET:
            raise ValueError("OCTO_SHOP_ID and OCTO_SECRET must be configured")

        payload = {
            "octo_shop_id": cls.SHOP_ID,
            "octo_secret": cls.SECRET,
            "transaction_id": transaction_id,
        }

        return cls._make_request("verificationInfo", payload)

    @classmethod
    def check_sms_key(
        cls,
        transaction_id: str,
        sms_key: str,
    ) -> Dict[str, Any]:
        """
        Verify OTP code.

        Args:
            transaction_id: OCTO transaction ID
            sms_key: OTP code from SMS

        Returns:
            Response from OCTO API
        """
        if not cls.SHOP_ID or not cls.SECRET:
            raise ValueError("OCTO_SHOP_ID and OCTO_SECRET must be configured")

        payload = {
            "octo_shop_id": cls.SHOP_ID,
            "octo_secret": cls.SECRET,
            "transaction_id": transaction_id,
            "sms_key": sms_key,
        }

        return cls._make_request("check_sms_key", payload)

    @classmethod
    def get_status(cls, transaction_id: str) -> Dict[str, Any]:
        """
        Get transaction status.

        Args:
            transaction_id: OCTO transaction ID

        Returns:
            Response from OCTO API with transaction status
        """
        if not cls.SHOP_ID or not cls.SECRET:
            raise ValueError("OCTO_SHOP_ID and OCTO_SECRET must be configured")

        payload = {
            "octo_shop_id": cls.SHOP_ID,
            "octo_secret": cls.SECRET,
            "transaction_id": transaction_id,
        }

        return cls._make_request("status", payload)

