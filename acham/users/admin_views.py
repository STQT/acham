"""Custom admin views for two-factor authentication."""

import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from acham.users.admin_forms import AdminLoginForm, AdminOTPForm
from acham.users.services.admin_otp_service import AdminOTPService
from acham.users.models import AdminOTP

logger = logging.getLogger(__name__)


@sensitive_post_parameters()
@csrf_protect
@never_cache
def admin_login_with_otp(request: HttpRequest) -> HttpResponse:
    """Custom admin login view with two-factor authentication via Telegram OTP."""
    
    # If user is already logged in and verified, redirect to admin
    if request.user.is_authenticated and request.user.is_staff:
        # Check if OTP verification is needed
        session_key = request.session.session_key
        if session_key:
            verified_otp = AdminOTP.objects.filter(
                session_key=session_key,
                user=request.user,
                verified_at__isnull=False,
            ).exists()
            
            if verified_otp:
                return redirect(reverse('admin:index'))
    
    # Handle GET request
    if request.method == 'GET':
        # Check if user wants to go back to login (clear OTP session)
        if request.GET.get('back_to_login'):
            request.session.pop('admin_otp_session_key', None)
            request.session.pop('admin_otp_user_id', None)
            request.session.pop('admin_remember_me', None)
        
        # Check if we're in OTP verification step
        session_key = request.session.get('admin_otp_session_key')
        user_id = request.session.get('admin_otp_user_id')
        
        if session_key and user_id:
            # Show OTP form
            form = AdminOTPForm(session_key=session_key)
            return render(request, 'admin/admin_otp.html', {
                'form': form,
                'title': _('Admin Login - OTP Verification'),
            })
        else:
            # Show login form
            form = AdminLoginForm()
            return render(request, 'admin/admin_login.html', {
                'form': form,
                'title': _('Admin Login'),
            })
    
    # Handle POST request
    if 'otp_code' in request.POST:
        # OTP verification step
        session_key = request.session.get('admin_otp_session_key')
        user_id = request.session.get('admin_otp_user_id')
        
        if not session_key or not user_id:
            messages.error(request, _('Session expired. Please login again.'))
            return redirect(reverse('admin:login'))
        
        form = AdminOTPForm(request.POST, session_key=session_key)
        
        if form.is_valid():
            code = form.cleaned_data['otp_code']
            
            # Verify OTP
            otp = AdminOTPService.verify_otp(session_key, code)
            
            if otp:
                # OTP verified successfully
                from acham.users.models import User
                from django.conf import settings
                try:
                    user = User.objects.get(pk=user_id)
                    
                    # Log the user in
                    # Use the first authentication backend (ModelBackend) for admin login
                    backend = settings.AUTHENTICATION_BACKENDS[0]
                    login(request, user, backend=backend)
                    
                    # Clean up session
                    request.session.pop('admin_otp_session_key', None)
                    request.session.pop('admin_otp_user_id', None)
                    
                    # Set session expiry based on remember_me
                    if request.session.get('admin_remember_me'):
                        request.session.set_expiry(1209600)  # 2 weeks
                    else:
                        request.session.set_expiry(0)  # Browser session
                    
                    logger.info(f"Admin user {user.email} logged in successfully with OTP")
                    
                    # Redirect to admin
                    next_url = request.GET.get('next', reverse('admin:index'))
                    return redirect(next_url)
                    
                except User.DoesNotExist:
                    messages.error(request, _('User not found.'))
            else:
                messages.error(request, _('Invalid or expired OTP code. Please try again.'))
        else:
            messages.error(request, _('Please correct the errors below.'))
        
        return render(request, 'admin/admin_otp.html', {
            'form': form,
            'title': _('Admin Login - OTP Verification'),
        })
    
    else:
        # Login step
        form = AdminLoginForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            
            # Ensure session exists
            if not request.session.session_key:
                request.session.create()
            
            session_key = request.session.session_key
            
            # Get client IP and user agent
            ip_address = None
            if hasattr(request, 'META'):
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0].strip()
                else:
                    ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Generate and send OTP
            try:
                otp = AdminOTPService.create_otp(
                    user=user,
                    session_key=session_key,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                
                # Store session info for OTP verification
                request.session['admin_otp_session_key'] = session_key
                request.session['admin_otp_user_id'] = user.id
                request.session['admin_remember_me'] = form.cleaned_data.get('remember_me', False)
                
                messages.success(request, _('OTP code has been sent to Telegram. Please check and enter the code.'))
                
                return redirect(reverse('admin:login'))
                
            except Exception as exc:
                logger.error(f"Failed to create OTP for admin login: {exc}", exc_info=True)
                messages.error(request, _('Failed to send OTP code. Please try again or contact administrator.'))
        
        return render(request, 'admin/admin_login.html', {
            'form': form,
            'title': _('Admin Login'),
        })
