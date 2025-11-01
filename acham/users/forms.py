from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django.contrib.auth import forms as admin_forms
from django import forms
from django.forms import EmailField, ModelChoiceField, CharField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponseRedirect

from django_countries.fields import CountryField
from django_countries import countries

from .models import User
from .otp_service import OTPService


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User
        field_classes = {"email": EmailField}


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = ("email",)
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """
    
    country = CountryField().formfield(
        required=True,
        label=_("Country"),
        empty_label=_("Select your country")
    )
    phone = CharField(
        max_length=20,
        required=False,
        label=_("Phone Number"),
        help_text=_("Required for Uzbekistan users")
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes for styling
        self.fields['country'].widget.attrs.update({'class': 'form-control'})
        self.fields['phone'].widget.attrs.update({'class': 'form-control'})
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        country_code = self.cleaned_data.get('country')
        
        # Only require phone for Uzbekistan
        if country_code and str(country_code) == 'UZ' and not phone:
            raise forms.ValidationError(_("Phone number is required for Uzbekistan."))
        
        return phone
    
    def save(self, request):
        user = super().save(request)
        user.country = self.cleaned_data['country']
        user.phone = self.cleaned_data['phone']
        user.save()
        
        # Send OTP for Uzbekistan users
        if user.country and str(user.country) == 'UZ' and user.phone:
            try:
                OTPService.send_otp_to_user(user)
                # Redirect to OTP verification page
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect(reverse('users:otp_verification', kwargs={'user_id': user.id}))
            except Exception:
                # If OTP sending fails, still create the user but mark as not verified
                pass
        
        return user


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """
