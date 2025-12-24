"""reCAPTCHA verification utility."""

import logging
from typing import Any

import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class RecaptchaError(Exception):
    """Raised when reCAPTCHA verification fails."""

    pass


def verify_recaptcha(token: str, remote_ip: str | None = None) -> dict[str, Any]:
    """
    Verify reCAPTCHA token with Google's API.
    
    Args:
        token: The reCAPTCHA token from the client
        remote_ip: Optional IP address of the user
        
    Returns:
        Response data from Google's API
        
    Raises:
        RecaptchaError: If verification fails
    """
    secret_key = getattr(settings, "RECAPTCHA_SECRET_KEY", None)
    
    if not secret_key:
        logger.warning("RECAPTCHA_SECRET_KEY is not configured. Skipping verification.")
        return {"success": True}  # Allow in development if not configured
    
    if not token:
        raise RecaptchaError(_("reCAPTCHA token is required."))
    
    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": secret_key,
        "response": token,
    }
    
    if remote_ip:
        data["remoteip"] = remote_ip
    
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if not result.get("success", False):
            error_codes = result.get("error-codes", [])
            logger.warning(f"reCAPTCHA verification failed: {error_codes}")
            raise RecaptchaError(_("reCAPTCHA verification failed. Please try again."))
        
        # Optional: Check score for reCAPTCHA v3 (threshold typically 0.5)
        score = result.get("score")
        if score is not None:
            threshold = getattr(settings, "RECAPTCHA_SCORE_THRESHOLD", 0.5)
            if score < threshold:
                logger.warning(f"reCAPTCHA score {score} below threshold {threshold}")
                raise RecaptchaError(_("reCAPTCHA verification failed. Please try again."))
        
        return result
        
    except requests.RequestException as exc:
        logger.error(f"Error verifying reCAPTCHA: {exc}")
        raise RecaptchaError(_("Error verifying reCAPTCHA. Please try again later.")) from exc

