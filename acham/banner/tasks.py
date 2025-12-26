from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import activate, get_language
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_subscription_confirmation_email(self, email: str, language: str = 'ru') -> dict:
    """
    Send confirmation email to newsletter subscriber.
    
    Args:
        email: Subscriber's email address
        language: Language code ('ru', 'en', 'uz')
    
    Returns:
        Dictionary with status
    """
    try:
        # Activate the requested language
        current_language = get_language()
        activate(language)
        
        # Subject lines by language
        subjects = {
            'ru': 'Подтверждение подписки на рассылку',
            'en': 'Subscription Confirmation',
            'uz': 'Obunani tasdiqlash',
        }
        
        # Template names by language
        template_name = f'banner/emails/subscription_confirmation_{language}.html'
        
        # Render HTML email template
        html_message = render_to_string(
            template_name,
            {'email': email}
        )
        # Generate plain text version
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subjects.get(language, subjects['ru']),
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Restore previous language
        activate(current_language)
        
        logger.info(f"Subscription confirmation email sent successfully to {email} in {language}")
        return {
            "status": "success",
            "email": email,
            "language": language,
        }
        
    except Exception as exc:
        logger.error(f"Failed to send subscription confirmation email to {email}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

