"""Celery tasks for order notifications."""

import logging
from typing import Any

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from acham.orders.models import Order
from acham.users.services.eskiz import EskizSMSClient, EskizConfigurationError, EskizAPIError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email(self, order_id: int, language: str | None = None) -> dict[str, Any]:
    """Send email notification when order is confirmed.
    
    Args:
        order_id: Order ID
        language: Language code (uz, ru, en). If None, uses default from settings.
    """
    try:
        order = Order.objects.select_related("user").prefetch_related("items").get(pk=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for email notification")
        return {"status": "error", "message": "Order not found"}

    # Get email from order or user
    email = order.customer_email or (order.user.email if order.user else None)
    
    if not email:
        logger.warning(f"No email found for order {order.number}")
        return {"status": "skipped", "message": "No email address available"}

    # Determine language
    if not language:
        # Try to get from order metadata or user preference, fallback to default
        language = getattr(settings, "LANGUAGE_CODE", "ru")[:2]  # Get first 2 chars (ru from ru-RU)
    
    # Validate language code
    available_languages = ["uz", "ru", "en"]
    if language not in available_languages:
        language = "ru"  # Default fallback

    try:
        # Activate language for translation
        translation.activate(language)
        
        try:
            # Prepare email context
            context = {
                "order": order,
                "order_items": order.items.all(),
                "site_name": getattr(settings, "SITE_NAME", "ACHAM Collection"),
            }

            # Render email template
            subject = _("Order Confirmation - {order_number}").format(order_number=order.number)
            message = render_to_string("orders/emails/order_confirmation.txt", context)
            html_message = render_to_string("orders/emails/order_confirmation.html", context)

            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Order confirmation email sent to {email} for order {order.number} (language: {language})")
            return {"status": "success", "email": email, "order_number": order.number, "language": language}
        finally:
            # Deactivate language
            translation.deactivate()

    except Exception as exc:
        logger.error(f"Failed to send order confirmation email: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_sms(self, order_id: int, language: str | None = None) -> dict[str, Any]:
    """Send SMS notification when order is confirmed.
    
    Args:
        order_id: Order ID
        language: Language code (uz, ru, en). If None, uses default from settings.
    """
    try:
        order = Order.objects.select_related("user").prefetch_related("items").get(pk=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for SMS notification")
        return {"status": "error", "message": "Order not found"}

    # Get phone from order or user
    phone = order.customer_phone or (order.user.phone if order.user else None)
    
    if not phone:
        logger.warning(f"No phone found for order {order.number}")
        return {"status": "skipped", "message": "No phone number available"}

    # Determine language
    if not language:
        # Try to get from order metadata or user preference, fallback to default
        language = getattr(settings, "LANGUAGE_CODE", "ru")[:2]  # Get first 2 chars (ru from ru-RU)
    
    # Validate language code
    available_languages = ["uz", "ru", "en"]
    if language not in available_languages:
        language = "ru"  # Default fallback

    try:
        # Activate language for translation
        translation.activate(language)
        
        try:
            # Initialize SMS client
            sms_client = EskizSMSClient()

            # Prepare SMS message with translation
            # This will be translated based on the activated language
            message = _(
                "Your order {order_number} has been confirmed. "
                "Total amount: {total_amount} {currency}. "
                "Thank you for your purchase!"
            ).format(
                order_number=order.number,
                total_amount=order.total_amount,
                currency=order.currency,
            )

            # Send SMS
            result = sms_client.send_sms(phone=phone, message=message)

            logger.info(f"Order confirmation SMS sent to {phone} for order {order.number} (language: {language})")
            return {"status": "success", "phone": phone, "order_number": order.number, "language": language, "result": result}
        finally:
            # Deactivate language
            translation.deactivate()

    except EskizConfigurationError as exc:
        logger.error(f"Eskiz not configured: {exc}")
        return {"status": "error", "message": "SMS service not configured"}
    except EskizAPIError as exc:
        logger.error(f"Eskiz API error: {exc}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
    except Exception as exc:
        logger.error(f"Failed to send order confirmation SMS: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def send_order_notification(self, order_id: int, language: str | None = None) -> dict[str, Any]:
    """
    Send order confirmation notification via email or SMS.
    Prioritizes email if available, otherwise sends SMS.
    
    Args:
        order_id: Order ID
        language: Language code (uz, ru, en). If None, uses default from settings.
    """
    try:
        order = Order.objects.select_related("user").prefetch_related("items").get(pk=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for notification")
        return {"status": "error", "message": "Order not found"}

    # Get contact information
    email = order.customer_email or (order.user.email if order.user else None)
    phone = order.customer_phone or (order.user.phone if order.user else None)

    # Determine language if not provided
    if not language:
        # Try to get from order metadata (if stored) or use default
        language = getattr(settings, "LANGUAGE_CODE", "ru")[:2]
    
    # Validate language code
    available_languages = ["uz", "ru", "en"]
    if language not in available_languages:
        language = "ru"  # Default fallback

    results = {}

    # Send email if available
    if email:
        try:
            email_task = send_order_confirmation_email.delay(order_id, language=language)
            results["email"] = {"status": "queued", "task_id": str(email_task.id), "language": language}
            logger.info(f"Order confirmation email queued for order {order.number}, task ID: {email_task.id}, language: {language}")
        except Exception as exc:
            logger.error(f"Failed to queue email notification: {exc}")
            results["email"] = {"status": "error", "message": str(exc)}
    else:
        # Send SMS if no email but phone is available
        if phone:
            try:
                sms_task = send_order_confirmation_sms.delay(order_id, language=language)
                results["sms"] = {"status": "queued", "task_id": str(sms_task.id), "language": language}
                logger.info(f"Order confirmation SMS queued for order {order.number}, task ID: {sms_task.id}, language: {language}")
            except Exception as exc:
                logger.error(f"Failed to queue SMS notification: {exc}")
                results["sms"] = {"status": "error", "message": str(exc)}
        else:
            logger.warning(f"No contact information available for order {order.number}")
            return {"status": "skipped", "message": "No email or phone available"}

    return {"status": "queued", "order_number": order.number, "language": language, "results": results}


@shared_task(bind=True, max_retries=3)
def send_order_status_update_email(
    self,
    order_id: int,
    old_status: str,
    new_status: str,
    language: str | None = None,
) -> dict[str, Any]:
    """Send email notification when order status changes.
    
    Args:
        order_id: Order ID
        old_status: Previous order status
        new_status: New order status
        language: Language code (uz, ru, en). If None, uses default from settings.
    """
    try:
        order = Order.objects.select_related("user").prefetch_related("items").get(pk=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for status update email")
        return {"status": "error", "message": "Order not found"}

    # Get email from order or user
    email = order.customer_email or (order.user.email if order.user else None)
    
    if not email:
        logger.warning(f"No email found for order {order.number}")
        return {"status": "skipped", "message": "No email address available"}

    # Determine language
    if not language:
        language = getattr(settings, "LANGUAGE_CODE", "ru")[:2]
    
    # Validate language code
    available_languages = ["uz", "ru", "en"]
    if language not in available_languages:
        language = "ru"

    try:
        # Activate language for translation
        translation.activate(language)
        
        try:
            # Status display names
            from acham.orders.models import OrderStatus as OS
            status_choices_dict = dict(OS.choices)
            old_status_display = status_choices_dict.get(old_status, old_status)
            new_status_display = status_choices_dict.get(new_status, new_status)

            # Prepare email context
            context = {
                "order": order,
                "order_items": order.items.all(),
                "old_status": old_status,
                "new_status": new_status,
                "old_status_display": old_status_display,
                "new_status_display": new_status_display,
                "site_name": getattr(settings, "SITE_NAME", "ACHAM Collection"),
            }

            # Render email template
            subject = _("Order {order_number} - Status Update").format(order_number=order.number)
            message = render_to_string("orders/emails/order_status_update.txt", context)
            html_message = render_to_string("orders/emails/order_status_update.html", context)

            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(
                f"Order status update email sent to {email} for order {order.number} "
                f"({old_status} → {new_status}, language: {language})"
            )
            return {
                "status": "success",
                "email": email,
                "order_number": order.number,
                "old_status": old_status,
                "new_status": new_status,
                "language": language,
            }
        finally:
            # Deactivate language
            translation.deactivate()

    except Exception as exc:
        logger.error(f"Failed to send order status update email: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def update_currency_rates(self) -> dict[str, Any]:
    """
    Update currency exchange rates from Central Bank of Uzbekistan API.
    Fetches rates from https://cbu.uz/uz/arkhiv-kursov-valyut/json/
    """
    from datetime import date
    from decimal import Decimal
    import requests
    from django.db import transaction as db_transaction
    
    from acham.orders.models import CurrencyRate
    
    try:
        # API endpoint for currency rates (JSON format)
        # Note: This endpoint returns today's rates by default
        api_url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
        
        logger.info(f"Fetching currency rates from {api_url}")
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        
        rates_data = response.json()
        today = date.today()
        updated_count = 0
        created_count = 0
        
        # CBU API structure:
        # - Ccy: Currency code (e.g., "USD", "EUR")
        # - Rate: Exchange rate (1 foreign currency = X UZS)
        # - Date: Date string
        with db_transaction.atomic():
            for rate_info in rates_data:
                code = rate_info.get('Ccy') or rate_info.get('code')
                if not code:
                    continue
                
                # CBU API returns rate as string, need to convert
                rate_str = rate_info.get('Rate') or rate_info.get('rate', '0')
                try:
                    rate = Decimal(str(rate_str))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid rate value for {code}: {rate_str}")
                    continue
                
                # Update or create currency rate
                # Note: We use code as unique identifier, and update date/rate if code exists
                currency_rate, created = CurrencyRate.objects.update_or_create(
                    code=code.upper(),
                    defaults={
                        'rate': rate,
                        'date': today,
                    }
                )
                
                if created:
                    created_count += 1
                    logger.info(f"Created currency rate: {code} = {rate} UZS")
                else:
                    updated_count += 1
                    logger.info(f"Updated currency rate: {code} = {rate} UZS")
        
        logger.info(f"Currency rates update completed: {created_count} created, {updated_count} updated")
        return {
            "status": "success",
            "created": created_count,
            "updated": updated_count,
            "date": str(today),
        }
        
    except requests.exceptions.RequestException as exc:
        logger.error(f"Failed to fetch currency rates: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
    except Exception as exc:
        logger.error(f"Error updating currency rates: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

