from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import update_session_auth_hash
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from django_countries import countries as django_countries

from acham.users.models import User
from acham.users.otp_service import OTPService

from .serializers import (
    UserSerializer, 
    UserRegistrationSerializer, 
    OTPVerificationSerializer,
    ResendOTPSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer
)
from drf_spectacular.utils import extend_schema, OpenApiTypes

User = get_user_model()


class CountryListView(APIView):
    """API endpoint to get list of available countries using django-countries."""
    permission_classes = [AllowAny]
    
    @extend_schema(responses={200: {'type': 'array', 'items': {'type': 'object'}}}}})
    def get(self, request):
        """
        Returns list of all countries with code, name, and phone verification requirement.
        Uzbekistan (UZ) requires phone verification.
        """
        country_list = []
        for code, name in django_countries:
            country_list.append({
                'code': code,
                'name': name,
                'requires_phone_verification': code == 'UZ'  # Only UZ requires phone
            })
        
        return Response(country_list)


class UserRegistrationView(APIView):
    """API endpoint for user registration with country selection."""
    permission_classes = [AllowAny]
    
    @extend_schema(request=UserRegistrationSerializer, responses={201: UserSerializer, 400: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Return user data with country info
            user_serializer = UserSerializer(user)
            response_data = {
                'user': user_serializer.data,
                'message': 'User registered successfully',
                'requires_otp': str(user.country) == 'UZ' if user.country else False
            }
            
            if user.country and str(user.country) == 'UZ':
                response_data['message'] = 'User registered successfully. OTP sent to your phone number.'
                response_data['otp_verification_url'] = f'/api/users/verify-otp/{user.id}/'
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerificationView(APIView):
    """API endpoint for OTP verification."""
    permission_classes = [AllowAny]
    
    @extend_schema(request=OTPVerificationSerializer, responses={200: UserSerializer, 400: OpenApiTypes.OBJECT})
    def post(self, request, user_id):
        data = request.data.copy()
        data['user_id'] = user_id
        
        serializer = OTPVerificationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Log the user in
            login(request, user)
            
            user_serializer = UserSerializer(user)
            return Response({
                'user': user_serializer.data,
                'message': 'Phone number verified successfully',
                'token': 'user_logged_in'  # You might want to return JWT token here
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    """API endpoint for resending OTP."""
    permission_classes = [AllowAny]
    
    @extend_schema(request=ResendOTPSerializer, responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            try:
                OTPService.send_otp_to_user(user)
                return Response({
                    'message': 'OTP sent successfully to your phone number'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "pk"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class ProfileMeViewSet(APIView):
    """
    API endpoint to retrieve, update, or delete current user's profile.
    Methods:
    GET    /api/users/me/
    PATCH  /api/users/me/
    DELETE /api/users/me/
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserProfileSerializer})
    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    @extend_schema(request=UserProfileSerializer, responses={200: UserProfileSerializer})
    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserProfileSerializer(user, context={"request": request}).data)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request):
        user = request.user
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    """
    Change password endpoint
    POST /api/users/change-password/
    Body: old_password, new_password1, new_password2
    Returns: 200 on success, 400 on validation error
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer, responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        update_session_auth_hash(request, request.user)  # Keeps session active if you want; optionally force logout
        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)


class JwtLogoutView(APIView):
    """
    JWT Logout endpoint (invalidate refresh token).
    POST /api/users/logout/
    Body: {"refresh": "<refresh_token>"}
    Returns 200 always.
    """
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        refresh_token = request.data.get('refresh', None)
        if not refresh_token:
            return Response({"detail": "No token provided"}, status=status.HTTP_200_OK)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass  # Token was already invalid or blacklisted
        except Exception:
            pass
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
