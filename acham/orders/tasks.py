"""Celery tasks for order notifications."""

import logging
from typing import Any

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from acham.orders.models import Order
from acham.users.services.eskiz import EskizSMSClient, EskizConfigurationError, EskizAPIError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email(self, order_id: int) -> dict[str, Any]:
    """Send email notification when order is confirmed."""
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

        logger.info(f"Order confirmation email sent to {email} for order {order.number}")
        return {"status": "success", "email": email, "order_number": order.number}

    except Exception as exc:
        logger.error(f"Failed to send order confirmation email: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_sms(self, order_id: int) -> dict[str, Any]:
    """Send SMS notification when order is confirmed."""
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

    try:
        # Initialize SMS client
        sms_client = EskizSMSClient()

        # Prepare SMS message
        site_name = getattr(settings, "SITE_NAME", "ACHAM Collection")
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

        logger.info(f"Order confirmation SMS sent to {phone} for order {order.number}")
        return {"status": "success", "phone": phone, "order_number": order.number, "result": result}

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
def send_order_notification(self, order_id: int) -> dict[str, Any]:
    """
    Send order confirmation notification via email or SMS.
    Prioritizes email if available, otherwise sends SMS.
    """
    try:
        order = Order.objects.select_related("user").prefetch_related("items").get(pk=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for notification")
        return {"status": "error", "message": "Order not found"}

    # Get contact information
    email = order.customer_email or (order.user.email if order.user else None)
    phone = order.customer_phone or (order.user.phone if order.user else None)

    results = {}

    # Send email if available
    if email:
        try:
            email_task = send_order_confirmation_email.delay(order_id)
            results["email"] = {"status": "queued", "task_id": str(email_task.id)}
            logger.info(f"Order confirmation email queued for order {order.number}, task ID: {email_task.id}")
        except Exception as exc:
            logger.error(f"Failed to queue email notification: {exc}")
            results["email"] = {"status": "error", "message": str(exc)}
    else:
        # Send SMS if no email but phone is available
        if phone:
            try:
                sms_task = send_order_confirmation_sms.delay(order_id)
                results["sms"] = {"status": "queued", "task_id": str(sms_task.id)}
                logger.info(f"Order confirmation SMS queued for order {order.number}, task ID: {sms_task.id}")
            except Exception as exc:
                logger.error(f"Failed to queue SMS notification: {exc}")
                results["sms"] = {"status": "error", "message": str(exc)}
        else:
            logger.warning(f"No contact information available for order {order.number}")
            return {"status": "skipped", "message": "No email or phone available"}

    return {"status": "queued", "order_number": order.number, "results": results}

