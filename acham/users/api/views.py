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

from acham.users.models import User, Country
from acham.users.otp_service import OTPService

from .serializers import (
    UserSerializer, 
    UserRegistrationSerializer, 
    CountrySerializer,
    OTPVerificationSerializer,
    ResendOTPSerializer
)

User = get_user_model()


class CountryListView(APIView):
    """API endpoint to get list of available countries."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        countries = Country.objects.all().order_by('name')
        serializer = CountrySerializer(countries, many=True)
        return Response(serializer.data)


class UserRegistrationView(APIView):
    """API endpoint for user registration with country selection."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Return user data with country info
            user_serializer = UserSerializer(user)
            response_data = {
                'user': user_serializer.data,
                'message': 'User registered successfully',
                'requires_otp': user.country.code == 'UZ' if user.country else False
            }
            
            if user.country and user.country.code == 'UZ':
                response_data['message'] = 'User registered successfully. OTP sent to your phone number.'
                response_data['otp_verification_url'] = f'/api/users/verify-otp/{user.id}/'
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerificationView(APIView):
    """API endpoint for OTP verification."""
    permission_classes = [AllowAny]
    
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
