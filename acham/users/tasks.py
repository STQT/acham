from celery import shared_task

from .models import User


@shared_task()
def get_users_count():
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()


@shared_task(bind=True, max_retries=3)
def send_bulk_email(self, subject: str, message: str, html_message: str | None = None, user_ids: list[int] | None = None) -> dict:
    """
    Send bulk email to users.
    
    Args:
        subject: Email subject
        message: Plain text email message
        html_message: Optional HTML email message
        user_ids: List of user IDs to send to. If None, sends to all users with email.
    
    Returns:
        Dictionary with status and statistics
    """
    from django.core.mail import send_mail
    from django.conf import settings
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Get users with email addresses
        if user_ids:
            users = User.objects.filter(id__in=user_ids, email__isnull=False).exclude(email="")
        else:
            users = User.objects.filter(email__isnull=False).exclude(email="")

        total_users = users.count()
        successful = 0
        failed = 0
        failed_emails = []

        for user in users:
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                successful += 1
                logger.info(f"Bulk email sent successfully to {user.email}")
            except Exception as exc:
                failed += 1
                failed_emails.append(user.email)
                logger.error(f"Failed to send email to {user.email}: {exc}")

        result = {
            "status": "completed",
            "total_users": total_users,
            "successful": successful,
            "failed": failed,
            "failed_emails": failed_emails,
        }

        logger.info(f"Bulk email completed: {successful} successful, {failed} failed out of {total_users} total")
        return result

    except Exception as exc:
        logger.error(f"Bulk email task failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
