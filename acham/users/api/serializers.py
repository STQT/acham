from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from acham.users.models import User, Country
from acham.users.otp_service import OTPService

User = get_user_model()


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'phone_code', 'requires_phone_verification']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    country = CountrySerializer(read_only=True)
    country_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password1', 'password2', 'name', 'phone', 'country', 'country_id']
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
            'phone': {'required': False},
        }
    
    def validate_password1(self, value):
        validate_password(value)
        return value
    
    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_phone(self, value):
        country_id = self.initial_data.get('country_id')
        if country_id:
            try:
                country = Country.objects.get(id=country_id)
                if country.code == 'UZ' and not value:
                    raise serializers.ValidationError("Phone number is required for Uzbekistan")
            except Country.DoesNotExist:
                pass
        return value
    
    def create(self, validated_data):
        country_id = validated_data.pop('country_id')
        password = validated_data.pop('password1')
        validated_data.pop('password2')
        
        try:
            country = Country.objects.get(id=country_id)
        except Country.DoesNotExist:
            raise serializers.ValidationError("Invalid country selected")
        
        user = User.objects.create_user(
            password=password,
            country=country,
            **validated_data
        )
        
        # Send OTP for Uzbekistan users
        if country.code == 'UZ' and user.phone:
            try:
                OTPService.send_otp_to_user(user)
            except Exception as e:
                # Log error but don't fail registration
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
        
        if not user.country or user.country.code != 'UZ':
            raise serializers.ValidationError("OTP verification is only available for Uzbekistan users")
        
        if not user.phone:
            raise serializers.ValidationError("User has no phone number")
        
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ["id", "name", "email", "phone", "country", "phone_verified", "url"]
        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "pk"},
        }
