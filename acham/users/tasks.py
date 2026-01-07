import secrets
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import User, PasswordResetToken


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


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id: int) -> dict:
    """
    Send password reset email to user.
    
    Args:
        user_id: User ID to send password reset email to
    
    Returns:
        Dictionary with status
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        user = User.objects.get(id=user_id)
        
        if not user.email:
            logger.warning(f"User {user_id} does not have an email address")
            return {"status": "error", "message": "User does not have an email address"}
        
        # Generate secure token
        token = secrets.token_urlsafe(48)
        
        # Create password reset token (expires in 24 hours)
        expires_at = timezone.now() + timedelta(hours=24)
        reset_token = PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at,
        )
        
        # Build reset URL
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200")
        reset_url = f"{frontend_url}/auth/reset-password?token={token}"
        
        # Get site name
        site_name = getattr(settings, "SITE_NAME", "ACHAM Collection")
        
        # Prepare email context
        context = {
            "user": user,
            "reset_url": reset_url,
            "site_name": site_name,
            "token": token,
        }
        
        # Render email templates
        subject = _("Password Reset Request")
        message = render_to_string("users/emails/password_reset.txt", context)
        html_message = render_to_string("users/emails/password_reset.html", context)
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent to {user.email}")
        return {"status": "success", "email": user.email}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {"status": "error", "message": "User not found"}
    except Exception as exc:
        logger.error(f"Failed to send password reset email: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
