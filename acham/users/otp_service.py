import random
import string
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class OTPService:
    """Service for handling OTP generation and verification."""
    
    @staticmethod
    def generate_otp(length=6):
        """Generate a random OTP code."""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def send_otp_to_phone(phone_number, otp_code):
        """
        Send OTP to phone number.
        In production, integrate with SMS service like Twilio, AWS SNS, etc.
        For now, we'll just log it or send via email for testing.
        """
        # TODO: Integrate with actual SMS service
        # For development/testing, we can log the OTP
        print(f"OTP for {phone_number}: {otp_code}")
        
        # You can also send via email for testing
        if hasattr(settings, 'ADMINS') and settings.ADMINS:
            admin_email = settings.ADMINS[0][1]
            send_mail(
                f'OTP Code for {phone_number}',
                f'Your OTP code is: {otp_code}',
                settings.DEFAULT_FROM_EMAIL,
                [admin_email],
                fail_silently=True,
            )
    
    @staticmethod
    def send_otp_to_user(user):
        """Send OTP to user's phone number (only for Uzbekistan users)."""
        if not user.phone:
            raise ValidationError("User has no phone number")
        
        # Only send OTP for Uzbekistan users
        if not user.country or user.country.code != 'UZ':
            raise ValidationError("OTP verification is only available for Uzbekistan users")
        
        otp_code = OTPService.generate_otp()
        user.otp_code = otp_code
        user.otp_expires_at = timezone.now() + timedelta(minutes=10)  # OTP expires in 10 minutes
        user.save()
        
        OTPService.send_otp_to_phone(user.phone, otp_code)
        return otp_code
    
    @staticmethod
    def verify_otp(user, provided_otp):
        """Verify OTP code for user."""
        if not user.otp_code or not user.otp_expires_at:
            return False
        
        if timezone.now() > user.otp_expires_at:
            return False
        
        if user.otp_code == provided_otp:
            user.phone_verified = 'Y'
            user.otp_code = ''
            user.otp_expires_at = None
            user.save()
            return True
        
        return False
    
    @staticmethod
    def is_otp_expired(user):
        """Check if user's OTP has expired."""
        if not user.otp_expires_at:
            return True
        return timezone.now() > user.otp_expires_at
