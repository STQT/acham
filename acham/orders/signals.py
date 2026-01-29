"""Signals for order-related events."""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from acham.orders.models import Order, OrderStatus, OrderStatusHistory
from acham.orders.tasks import send_order_status_update_email, send_order_telegram_notification

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Order)
def track_order_status_change(sender, instance, **kwargs):
    """Track order status changes before saving."""
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def send_status_update_notification(sender, instance, created, **kwargs):
    """Send notifications when order is created or status changes."""
    if created:
        # Do not send Telegram notification on creation (order is usually PENDING_PAYMENT at this point).
        # We send the same "new order" Telegram message when payment is confirmed instead.
        return

    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    # If status changed, send notification
    if old_status and old_status != new_status:
        # Create status history entry
        OrderStatusHistory.objects.create(
            order=instance,
            from_status=old_status,
            to_status=new_status,
            note="Status updated",
        )

        # Send email notification if customer email is available
        if instance.customer_email:
            try:
                # Determine language (you can enhance this to get from user preferences)
                language = "ru"  # Default language
                
                # Queue the email task
                send_order_status_update_email.delay(
                    order_id=instance.pk,
                    old_status=old_status,
                    new_status=new_status,
                    language=language,
                )
                logger.info(
                    f"Queued status update email for order {instance.number} "
                    f"({old_status} → {new_status})"
                )
            except Exception as exc:
                logger.error(
                    f"Failed to queue status update email for order {instance.number}: {exc}",
                    exc_info=True,
                )
        
        # Telegram notifications:
        # - Do NOT notify when status becomes PENDING_PAYMENT
        # - Send the "new order" message when status becomes PAYMENT_CONFIRMED
        # - For other statuses keep status_update notifications
        if new_status == OrderStatus.PENDING_PAYMENT:
            return

        if new_status == OrderStatus.PAYMENT_CONFIRMED:
            try:
                send_order_telegram_notification.delay(instance.pk, message_type="new")
                logger.info(f"Queued Telegram notification for PAID order {instance.number}")
            except Exception as exc:
                logger.error(
                    f"Failed to queue Telegram notification for PAID order {instance.number}: {exc}",
                    exc_info=True,
                )
            return

        # Send Telegram notification for other status updates
        # try:
        #     send_order_telegram_notification.delay(instance.pk, message_type="status_update")
        #     logger.info(
        #         f"Queued Telegram status update notification for order {instance.number} "
        #         f"({old_status} → {new_status})"
        #     )
        # except Exception as exc:
        #     logger.error(
        #         f"Failed to queue Telegram status update notification for order {instance.number}: {exc}",
        #         exc_info=True,
        #     )
