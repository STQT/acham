"""Service for interacting with OCTO payment gateway API."""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Any, Dict, List

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class OctoService:
    @staticmethod
    def _get_api_url():
        return getattr(settings, "OCTO_API_URL", "https://secure.octo.uz")

    @staticmethod
    def _get_shop_id():
        return getattr(settings, "OCTO_SHOP_ID", None)

    @staticmethod
    def _get_secret():
        return getattr(settings, "OCTO_SECRET", None)

    @staticmethod
    def _get_test_mode():
        return getattr(settings, "OCTO_TEST_MODE", False)

    @classmethod
    def _send_request(cls, method: str, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        logger.info(f"OCTO API request: {method} {url}")
        logger.info(f"OCTO API request headers: {headers}")
        logger.info(f"OCTO API request data: {json.dumps(data)}")

        try:
            response = requests.request(method, url, headers=headers, json=data, timeout=30)

            # Логируем статус и тело ответа
            logger.info(f"OCTO API response status: {response.status_code}")
            logger.info(f"OCTO API response headers: {dict(response.headers)}")

            try:
                response_json = response.json()
                logger.info(f"OCTO API response body: {json.dumps(response_json)}")
            except (ValueError, json.JSONDecodeError):
                response_text = response.text[:1000]  # Ограничиваем длину текста
                logger.info(f"OCTO API response body (not JSON): {response_text}")
                response_json = {}

            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response_json
        except requests.exceptions.HTTPError as e:
            # Для HTTP ошибок логируем полный ответ
            error_response = {}
            try:
                error_response = e.response.json() if e.response else {}
                logger.error(f"OCTO API HTTP error ({url}): Status {e.response.status_code if e.response else 'N/A'}, Response: {json.dumps(error_response)}")
            except (ValueError, json.JSONDecodeError, AttributeError):
                error_text = e.response.text[:1000] if e.response else str(e)
                logger.error(f"OCTO API HTTP error ({url}): Status {e.response.status_code if e.response else 'N/A'}, Response (not JSON): {error_text}")

            return {"error": e.response.status_code if e.response else -1, "errMessage": error_response.get("errMessage", str(e))}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending request to OCTO ({url}): {e}", exc_info=True)
            return {"error": -1, "errMessage": str(e)}

    @classmethod
    def prepare_payment(
        cls,
        shop_transaction_id: str,
        total_sum: Decimal,
        user_data: Dict[str, str],
        basket: List[Dict[str, Any]],
        return_url: str,
        notify_url: str,
        language: str = "uz",
        description: str = "",
        auto_capture: bool = True,
        ttl: int = 15, # minutes
        init_time: str = None,
    ) -> Dict[str, Any]:
        url = f"{cls._get_api_url()}/prepare_payment"
        payload = {
            "octo_shop_id": cls._get_shop_id(),
            "octo_secret": cls._get_secret(),
            "shop_transaction_id": shop_transaction_id,
            "auto_capture": auto_capture,
            "test": cls._get_test_mode(),
            "user_data": user_data,
            "total_sum": float(total_sum),
            "currency": "UZS",  # Assuming fixed currency for now
            "description": description,
            "basket": basket,
            "payment_methods": [
                {"method": "bank_card"},
                {"method": "uzcard"},
                {"method": "humo"},
            ],
            "return_url": return_url,
            "notify_url": notify_url,
            "language": language,
            "ttl": ttl,
        }

        # Add init_time if provided
        if init_time:
            payload["init_time"] = init_time
        logger.info(f"Sending prepare_payment to OCTO: {json.dumps(payload)}")
        return cls._send_request("POST", url, payload)

    @classmethod
    def pay(cls, transaction_id: str, card_data: Dict[str, str]) -> Dict[str, Any]:
        shop_id = cls._get_shop_id()
        secret = cls._get_secret()

        logger.info(f"OCTO Config - Shop ID: {shop_id}, API URL: {cls._get_api_url()}, Test Mode: {cls._get_test_mode()}")

        if not shop_id or not secret:
            logger.error("OCTO credentials not configured!")
            return {"error": -1, "errMessage": "OCTO credentials not configured"}

        # For test mode, simulate successful payment
        if cls._get_test_mode():
            logger.info("TEST MODE: Simulating successful payment")
            return {
                "error": 0,
                "data": {
                    "status": "success",
                    "transaction_id": transaction_id,
                    "message": "Test payment processed successfully"
                }
            }

        url = f"{cls._get_api_url()}/pay"
        payload = {
            "octo_shop_id": shop_id,
            "octo_secret": "***",  # Don't log the actual secret
            "transaction_id": transaction_id,
            "card_data": card_data,
        }
        logger.info(f"Sending pay to OCTO: {json.dumps(payload)}")
        return cls._send_request("POST", url, payload)

    @classmethod
    def verification_info(cls, transaction_id: str) -> Dict[str, Any]:
        # For test mode, simulate successful verification
        if cls._get_test_mode():
            logger.info("TEST MODE: Simulating successful verification")
            return {
                "error": 0,
                "data": {
                    "id": transaction_id,
                    "verification_url": "https://test.octo.uz/verify",
                    "secondsLeft": 300,
                    "status": "verification_required"
                }
            }

        url = f"{cls._get_api_url()}/verificationInfo"
        payload = {
            "octo_shop_id": cls._get_shop_id(),
            "octo_secret": cls._get_secret(),
            "transaction_id": transaction_id,
        }
        logger.info(f"Sending verificationInfo to OCTO: {json.dumps(payload)}")
        return cls._send_request("POST", url, payload)

    @classmethod
    def check_sms_key(cls, transaction_id: str, sms_key: str) -> Dict[str, Any]:
        url = f"{cls._get_api_url()}/check_sms_key"
        payload = {
            "octo_shop_id": cls._get_shop_id(),
            "octo_secret": cls._get_secret(),
            "transaction_id": transaction_id,
            "sms_key": sms_key,
        }
        logger.info(f"Sending check_sms_key to OCTO: {json.dumps(payload)}")
        return cls._send_request("POST", url, payload)

    @classmethod
    def check_transaction(cls, transaction_id: str) -> Dict[str, Any]:
        url = f"{cls._get_api_url()}/check_transaction"
        payload = {
            "octo_shop_id": cls._get_shop_id(),
            "octo_secret": cls._get_secret(),
            "transaction_id": transaction_id,
        }
        logger.info(f"Sending check_transaction to OCTO: {json.dumps(payload)}")
        return cls._send_request("POST", url, payload)

