
from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for ACHAM Collection.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    REGISTRATION_EMAIL = "email"
    REGISTRATION_PHONE = "phone"
    REGISTRATION_SOCIAL = "social"

    REGISTRATION_METHOD_CHOICES = [
        (REGISTRATION_EMAIL, _("Email")),
        (REGISTRATION_PHONE, _("Phone OTP")),
        (REGISTRATION_SOCIAL, _("Social Network")),
    ]

    # First and last name do not cover name patterns around the globe
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = models.EmailField(_("email address"), blank=True, null=True)
    phone_validator = RegexValidator(
        regex=r"^\+?[1-9]\d{7,14}$",
        message=_("Enter a valid international phone number starting with country code."),
    )
    phone = models.CharField(
        _("phone number"),
        blank=True,
        null=True,
        max_length=20,
        validators=[phone_validator],
    )
    username = None  # type: ignore[assignment]
    registration_method = models.CharField(
        _("Registration method"),
        max_length=20,
        choices=REGISTRATION_METHOD_CHOICES,
        default=REGISTRATION_EMAIL,
        help_text=_("Method used for user registration"),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    class Meta(AbstractUser.Meta):  # type: ignore[misc]
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(email__isnull=False),
                name="users_unique_email",
            ),
            models.UniqueConstraint(
                fields=["phone"],
                condition=models.Q(phone__isnull=False),
                name="users_unique_phone",
            ),
        ]

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})

    def __str__(self) -> str:
        """Human readable representation that never returns None."""
        return self.name or self.email or self.phone or f"User {self.pk}"


class PhoneOTP(models.Model):
    """Stores one-time passwords for phone verification and login."""

    PURPOSE_REGISTRATION = "registration"
    PURPOSE_LOGIN = "login"

    PURPOSE_CHOICES = [
        (PURPOSE_REGISTRATION, _("Registration")),
        (PURPOSE_LOGIN, _("Login")),
    ]

    phone = models.CharField(_("phone number"), max_length=20)
    purpose = models.CharField(_("Purpose"), max_length=32, choices=PURPOSE_CHOICES)
    code_hash = models.CharField(_("OTP hash"), max_length=128)
    expires_at = models.DateTimeField(_("Expires at"))
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    verified_at = models.DateTimeField(_("Verified at"), blank=True, null=True)
    attempts = models.PositiveSmallIntegerField(_("Attempts"), default=0)
    is_active = models.BooleanField(_("Is active"), default=True)

    class Meta:
        indexes = [
            models.Index(fields=["phone", "purpose", "is_active"]),
            models.Index(fields=["expires_at"]),
        ]
        verbose_name = _("Phone OTP")
        verbose_name_plural = _("Phone OTPs")

    def __str__(self) -> str:
        return f"{self.phone} ({self.purpose})"
