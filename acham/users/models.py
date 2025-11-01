
from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.db.models import EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for ACHAM Collection.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """
    
    email = EmailField(_("email address"), unique=True)
    phone = CharField(_("phone number"), blank=True, max_length=255)
    country = CountryField(blank=True, verbose_name=_("Country"))
    phone_verified = CharField(
        _("Phone Verified"),
        max_length=1,
        choices=[('Y', 'Yes'), ('N', 'No')],
        default='N'
    )
    otp_code = CharField(_("OTP Code"), blank=True, max_length=6)
    otp_expires_at = models.DateTimeField(_("OTP Expires At"), null=True, blank=True)
    username = None  # type: ignore[assignment]
    # Standard Django user names
    first_name = CharField(_("first name"), max_length=150,null=True, blank=False)
    last_name = CharField(_("last name"), max_length=150,null=True, blank=False)
    gender = CharField(
        _("Gender"),
        max_length=6,
        choices=[('male', 'Male'), ('female', 'Female')],
        null=True,
        blank=False,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view."""
        return reverse("users:detail", kwargs={"pk": self.id})
