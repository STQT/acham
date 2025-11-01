from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django_countries import countries

from acham.users.models import User
from acham.users.otp_service import OTPService

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    country = serializers.CharField(max_length=2, write_only=True, required=True)
    country_display = serializers.CharField(source='country.name', read_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    gender = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')])

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2', 'first_name', 'last_name', 'gender', 'phone', 'country', 'country_display']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'gender': {'required': True},
            'phone': {'required': False},
        }

    def validate_password1(self, value):
        validate_password(value)
        return value

    def validate_country(self, value):
        """Validate country code."""
        if value not in countries:
            raise serializers.ValidationError("Invalid country code")
        return value

    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate phone for Uzbekistan
        country_code = attrs.get('country', '')
        if country_code == 'UZ' and not attrs.get('phone'):
            raise serializers.ValidationError({"phone": "Phone number is required for Uzbekistan"})
        
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password1')
        validated_data.pop('password2')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Send OTP for Uzbekistan users
        if user.country and str(user.country) == 'UZ' and user.phone:
            try:
                OTPService.send_otp_to_user(user)
            except Exception:
                pass
        
        return user


class OTPVerificationSerializer(serializers.Serializer):
    otp_code = serializers.CharField(max_length=6, min_length=6)
    user_id = serializers.IntegerField()
    
    def validate_otp_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP code must contain only digits")
        return value
    
    def validate(self, attrs):
        user_id = attrs['user_id']
        otp_code = attrs['otp_code']
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        
        if not OTPService.verify_otp(user, otp_code):
            raise serializers.ValidationError("Invalid or expired OTP code")
        
        attrs['user'] = user
        return attrs


class ResendOTPSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    
    def validate(self, attrs):
        user_id = attrs['user_id']
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        
        if not user.country or str(user.country) != 'UZ':
            raise serializers.ValidationError("OTP verification is only available for Uzbekistan users")
        
        if not user.phone:
            raise serializers.ValidationError("User has no phone number")
        
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    country = serializers.CharField(source='country.code', read_only=True)
    country_display = serializers.CharField(source='country.name', read_only=True)
    
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "phone", "country", "country_display", "phone_verified", "url"]
        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "pk"},
        }


class UserProfileSerializer(serializers.ModelSerializer):
    country = serializers.CharField(source='country.code', read_only=True)
    country_display = serializers.CharField(source='country.name', read_only=True)
    country_code = serializers.CharField(write_only=True, required=False, max_length=2)
    gender = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')], required=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "gender", "email", "phone", "country", "country_display", "country_code", "phone_verified", "url"]
        read_only_fields = ['id', 'phone_verified', 'url', 'country', 'country_display']

    def validate_country_code(self, value):
        """Validate country code."""
        if value and value not in countries:
            raise serializers.ValidationError("Invalid country code")
        return value

    def update(self, instance, validated_data):
        country_code = validated_data.pop('country_code', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if country_code is not None:
            instance.country = country_code
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({'old_password': 'Wrong password.'})
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({'new_password2': 'Passwords do not match.'})
        validate_password(data['new_password1'], user)
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password1'])
        user.save()
        return user
