"""Forms for admin two-factor authentication."""

from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


class AdminLoginForm(forms.Form):
    """Form for admin login with email/password."""
    
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Email address'),
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Password'),
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label=_("Remember me"),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(
                self.request,
                username=email,
                password=password,
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    _("Please enter a correct email and password. "
                      "Note that both fields may be case-sensitive.")
                )
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_("This account is inactive."))
            elif not self.user_cache.is_staff:
                raise forms.ValidationError(
                    _("You don't have permission to access the admin site.")
                )

        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class AdminOTPForm(forms.Form):
    """Form for entering OTP code."""
    
    otp_code = forms.CharField(
        label=_("OTP Code"),
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter 6-digit code'),
            'autofocus': True,
            'autocomplete': 'off',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
        }),
        help_text=_("Enter the 6-digit code sent to Telegram"),
    )

    def __init__(self, session_key=None, *args, **kwargs):
        self.session_key = session_key
        super().__init__(*args, **kwargs)

    def clean_otp_code(self):
        code = self.cleaned_data.get('otp_code')
        if code:
            # Remove any spaces or dashes
            code = code.replace(' ', '').replace('-', '')
            if not code.isdigit():
                raise forms.ValidationError(_("OTP code must contain only digits."))
            if len(code) != 6:
                raise forms.ValidationError(_("OTP code must be 6 digits."))
        return code
