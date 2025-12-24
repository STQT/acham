import re
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from acham.users.models import PhoneOTP
from acham.users.services.otp import OTPError
from acham.users.services.otp import send_phone_otp
from acham.users.services.otp import verify_phone_otp
from acham.users.services.recaptcha import RecaptchaError
from acham.users.services.recaptcha import verify_recaptcha

User = get_user_model()


def normalize_phone(value: str) -> str:
    cleaned = re.sub(r"[^\d]", "", value)
    if cleaned.startswith("00"):
        cleaned = cleaned[2:]
    if not cleaned:
        return value

    if len(cleaned) == 9 and cleaned.isdigit():
        cleaned = f"998{cleaned}"

    if not cleaned.startswith("+"):
        cleaned = f"+{cleaned}"

    return cleaned


def phone_lookup_variants(phone: str) -> set[str]:
    normalized = normalize_phone(phone)
    variants: set[str] = {normalized}

    digits = normalized[1:] if normalized.startswith("+") else normalized
    variants.add(digits)

    if digits.startswith("998") and len(digits) > 3:
        local = digits[3:]
        variants.update({local, f"+{local}", f"998{local}"})

    return {variant for variant in variants if variant}


def find_user_by_phone(phone: str) -> User | None:
    variants = phone_lookup_variants(phone)
    return User.objects.filter(phone__in=variants).first()


def ensure_user_exists_for_phone(phone: str) -> User:
    user = find_user_by_phone(phone)
    if user:
        return user

    normalized = normalize_phone(phone)
    password = get_random_string(20)
    return User.objects.create_user(phone=normalized, email=None, password=password)


class UserSerializer(serializers.ModelSerializer[User]):
    phone = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "phone", "name", "is_active"]
        read_only_fields = ["id", "is_active"]

    def get_phone(self, obj: User) -> str | None:
        phone_value = getattr(obj, "phone", None)
        if not phone_value:
            return None
        phone_str = str(phone_value)
        cleaned = re.sub(r"[^\d]", "", phone_str)
        if cleaned.startswith("998"):
            return f"+{cleaned}"
        if phone_str.startswith("+"):
            return phone_str
        return f"+{phone_str}"


class UserUpdateSerializer(serializers.ModelSerializer[User]):
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = ["name", "email", "phone"]

    def validate_email(self, value: str | None) -> str | None:
        if not value:
            return None
        email_lower = value.lower()
        qs = User.objects.filter(email__iexact=email_lower)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(_("User with this email already exists."))
        return email_lower

    def validate_phone(self, value: str | None) -> str | None:
        if not value:
            return None
        normalized = normalize_phone(value)
        User.phone_validator(normalized)
        qs = User.objects.filter(phone=normalized)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(_("User with this phone already exists."))
        return normalized

    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        instance.name = validated_data.get("name", instance.name)
        instance.email = validated_data.get("email", instance.email)
        instance.phone = validated_data.get("phone", instance.phone)
        instance.save(update_fields=["name", "email", "phone"])
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=8)

    default_error_messages = {
        "incorrect_password": _("Current password is incorrect."),
    }

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            self.fail("incorrect_password")
        return value

    def validate_new_password(self, value: str) -> str:
        password_validation.validate_password(value, user=self.context["request"].user)
        return value

    def save(self, **kwargs) -> User:
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class EmailRegistrationSerializer(serializers.ModelSerializer[User]):
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "password", "name", "phone"]

    def validate_email(self, value: str | None) -> str:
        if not value:
            raise serializers.ValidationError(_("Email is required."))
        email_lower = value.lower()
        if User.objects.filter(email__iexact=email_lower).exists():
            raise serializers.ValidationError(_("User with this email already exists."))
        return email_lower

    def validate_phone(self, value: str | None) -> str | None:
        if not value:
            return None
        normalized = normalize_phone(value)
        User.phone_validator(normalized)
        if User.objects.filter(phone=normalized).exists():
            raise serializers.ValidationError(_("User with this phone already exists."))
        return normalized

    def validate_password(self, value: str) -> str:
        password_validation.validate_password(value, user=None)
        return value

    def create(self, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop("password")
        if not validated_data.get("phone"):
            validated_data.pop("phone", None)
        return User.objects.create_user(password=password, **validated_data)


class PhoneRegistrationConfirmSerializer(serializers.Serializer[dict[str, Any]]):
    phone = serializers.CharField(validators=[User.phone_validator])
    code = serializers.CharField(min_length=4, max_length=6)
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)

    default_error_messages = {
        "invalid_code": _("Invalid or expired OTP code."),
        "user_exists": _("User with this phone already exists."),
    }

    def validate_phone(self, value: str) -> str:
        normalized = normalize_phone(value)
        User.phone_validator(normalized)
        if User.objects.filter(phone=normalized).exists():
            self.fail("user_exists")
        return normalized

    def validate_password(self, value: str) -> str:
        password_validation.validate_password(value, user=None)
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        phone = attrs.get("phone")
        code = attrs.get("code")
        if not phone or not code:
            return attrs
        try:
            verify_phone_otp(phone=phone, purpose=PhoneOTP.PURPOSE_REGISTRATION, code=code)
        except OTPError as exc:
            raise serializers.ValidationError({"code": str(exc)}) from exc
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop("password")
        validated_data.pop("code", None)
        email = validated_data.get("email") or None
        if email:
            validated_data["email"] = email.lower()
        return User.objects.create_user(password=password, **validated_data)


class PhoneOTPLoginRequestSerializer(serializers.Serializer[dict[str, str]]):
    phone = serializers.CharField(validators=[User.phone_validator])
    recaptcha_token = serializers.CharField(required=True, write_only=True)

    default_error_messages = {
        "not_found": _("User with this phone number does not exist."),
        "inactive": _("User account is disabled."),
        "recaptcha_required": _("reCAPTCHA verification is required."),
    }

    def validate_recaptcha_token(self, value: str) -> str:
        """Validate reCAPTCHA token before processing the request."""
        if not value:
            raise serializers.ValidationError(self.error_messages["recaptcha_required"])
        
        request = self.context.get("request")
        remote_ip = None
        if request:
            # Get client IP address
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                remote_ip = x_forwarded_for.split(",")[0].strip()
            else:
                remote_ip = request.META.get("REMOTE_ADDR")
        
        try:
            verify_recaptcha(token=value, remote_ip=remote_ip)
        except RecaptchaError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        
        return value

    def validate_phone(self, value: str) -> str:
        normalized = normalize_phone(value)
        User.phone_validator(normalized)
        user = find_user_by_phone(normalized)
        if user and not user.is_active:
            raise serializers.ValidationError({"phone": self.error_messages["inactive"]})
        self.context["user"] = user
        return normalized

    def create(self, validated_data: dict[str, str]) -> dict[str, str]:
        # Remove recaptcha_token from validated_data as it's not needed after validation
        validated_data.pop("recaptcha_token", None)
        
        phone = validated_data["phone"]
        purpose = PhoneOTP.PURPOSE_LOGIN
        try:
            send_phone_otp(phone=phone, purpose=purpose)
        except OTPError as exc:
            raise serializers.ValidationError({"phone": str(exc)}) from exc
        validated_data["is_new_user"] = self.context.get("user") is None
        return validated_data


class PhoneOTPVerifySerializer(serializers.Serializer[dict[str, str]]):
    phone = serializers.CharField(validators=[User.phone_validator])
    code = serializers.CharField(min_length=4, max_length=6)

    def validate(self, attrs: dict[str, str]) -> dict[str, str]:
        phone = normalize_phone(attrs["phone"])
        User.phone_validator(phone)
        attrs["phone"] = phone
        try:
            otp = verify_phone_otp(phone=phone, purpose=PhoneOTP.PURPOSE_LOGIN, code=attrs["code"])
        except OTPError as exc:
            raise serializers.ValidationError({"code": str(exc)}) from exc
        user = ensure_user_exists_for_phone(otp.phone)
        attrs["user"] = user
        return attrs


class EmailPhoneTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop(self.username_field, None)

    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    default_error_messages = {
        "no_active_account": _("No active account found with the given credentials."),
    }

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        identifier = attrs.get("identifier", "").strip()
        password = attrs.get("password")

        if not identifier or not password:
            raise AuthenticationFailed(self.error_messages["no_active_account"])

        user = self._get_user(identifier)
        if user is None or not user.check_password(password) or not user.is_active:
            raise AuthenticationFailed(self.error_messages["no_active_account"])

        refresh = self.get_token(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user, context=self.context).data,
        }
        return data

    @staticmethod
    def _get_user(identifier: str) -> User | None:
        if "@" in identifier:
            try:
                return User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                return None
        phone = normalize_phone(identifier)
        try:
            return User.objects.get(phone=phone)
        except User.DoesNotExist:
            return None
