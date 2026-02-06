from rest_framework import generics
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError

from ..models import FAQ, StaticPage, ContactMessage, ReturnRequest, EmailSubscription, AboutPageSection
from .serializers import (
    FAQSerializer, 
    StaticPageSerializer, 
    ContactMessageSerializer, 
    ReturnRequestSerializer, 
    EmailSubscriptionSerializer,
    AboutPageSectionSerializer
)
from ..tasks import send_subscription_confirmation_email


@extend_schema(
    tags=['faqs'],
    summary="List all FAQs",
    description="Retrieve a list of all frequently asked questions."
)
class FAQListView(generics.ListAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer


@extend_schema(
    tags=['faqs'],
    summary="Retrieve FAQ details",
    description="Retrieve detailed information about a specific FAQ by ID."
)
class FAQDetailView(generics.RetrieveAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer


@extend_schema(
    tags=['static-pages'],
    summary="Retrieve static page by type",
    description="Retrieve a static page by its type (terms, privacy_policy, acham_history, work_with_us)."
)
class StaticPageByTypeView(generics.RetrieveAPIView):
    """Retrieve a static page by its type."""
    queryset = StaticPage.objects.all()
    serializer_class = StaticPageSerializer
    lookup_field = 'page_type'
    lookup_url_kwarg = 'page_type'


@extend_schema(
    tags=['static-pages'],
    summary="List all static pages",
    description="Retrieve a list of all static pages."
)
class StaticPageListView(generics.ListAPIView):
    queryset = StaticPage.objects.all()
    serializer_class = StaticPageSerializer


@extend_schema(
    tags=['contact'],
    summary="Submit contact form",
    description="Submit a contact form message."
)
class ContactMessageCreateView(generics.CreateAPIView):
    """Create a new contact message."""
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = []  # Allow anonymous users to submit contact forms


@extend_schema(
    tags=['returns'],
    summary="Submit return request",
    description="Submit a return request form."
)
class ReturnRequestCreateView(generics.CreateAPIView):
    """Create a new return request."""
    queryset = ReturnRequest.objects.all()
    serializer_class = ReturnRequestSerializer
    permission_classes = []  # Allow anonymous users to submit return requests


@extend_schema(
    tags=['newsletter'],
    summary="Subscribe to email newsletter",
    description="Subscribe an email address to the newsletter mailing list."
)
class EmailSubscriptionCreateView(generics.CreateAPIView):
    """Create a new email subscription."""
    queryset = EmailSubscription.objects.all()
    serializer_class = EmailSubscriptionSerializer
    permission_classes = []  # Allow anonymous users to subscribe
    
    def _get_request_language(self, request):
        """Extract language from request headers or query params."""
        # Try to get from Accept-Language header
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        
        # Parse Accept-Language header (e.g., "ru-RU,ru;q=0.9,en-US;q=0.8")
        if accept_language:
            # Get first language code
            lang_code = accept_language.split(',')[0].split('-')[0].split(';')[0].strip().lower()
            # Validate against supported languages
            if lang_code in ['ru', 'en', 'uz']:
                return lang_code
        
        # Default to Russian
        return 'ru'
    
    def create(self, request, *args, **kwargs):
        """Handle subscription creation with duplicate email handling."""
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'email': ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get language from request
        language = self._get_request_language(request)
        
        # Check if email already exists
        existing_subscription = EmailSubscription.objects.filter(email=email).first()
        
        if existing_subscription:
            # If exists but inactive, reactivate it
            if not existing_subscription.is_active:
                existing_subscription.is_active = True
                existing_subscription.language = language  # Update language
                existing_subscription.save()
                # Send confirmation email asynchronously
                send_subscription_confirmation_email.delay(email, language)
                serializer = self.get_serializer(existing_subscription)
                return Response(serializer.data, status=status.HTTP_200_OK)
            # If already active, return success with existing data
            serializer = self.get_serializer(existing_subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Create new subscription with language
        serializer = self.get_serializer(data={'email': email, 'language': language})
        serializer.is_valid(raise_exception=True)
        
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            # Send confirmation email asynchronously for new subscription
            send_subscription_confirmation_email.delay(email, language)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except IntegrityError:
            # Handle race condition where email was created between check and save
            existing_subscription = EmailSubscription.objects.get(email=email)
            serializer = self.get_serializer(existing_subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['about-page'],
    summary="Get about page data",
    description="Retrieve the complete about page data (singleton model)."
)
class AboutPageSectionListView(generics.RetrieveAPIView):
    """Get the singleton about page instance."""
    serializer_class = AboutPageSectionSerializer
    
    def get_object(self):
        """Return the singleton instance."""
        return AboutPageSection.get_instance()


@extend_schema(
    tags=['about-page'],
    summary="Get complete about page data",
    description="Retrieve all about page sections in a single response."
)
class AboutPageView(generics.GenericAPIView):
    """Get complete about page data with all sections."""
    serializer_class = AboutPageSectionSerializer
    
    def get(self, request, *args, **kwargs):
        """Return the singleton instance with all sections."""
        instance = AboutPageSection.get_instance()
        
        if not instance.is_active:
            return Response(
                {'detail': 'About page is not active.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance)
        
        # Organize data by sections for easier frontend consumption
        data = serializer.data
        organized_data = {
            'hero': {
                'founder_name': data.get('founder_name'),
                'founder_title': data.get('founder_title'),
                'hero_image': data.get('hero_image'),
                'hero_image_url': data.get('hero_image_url'),
            },
            'history': {
                'title': data.get('history_title'),
                'content': data.get('history_content'),
                'image': data.get('history_image'),
                'image_url': data.get('history_image_url'),
            },
            'philosophy': {
                'title': data.get('philosophy_title'),
                'content': data.get('philosophy_content'),
                'image': data.get('philosophy_image'),
                'image_url': data.get('philosophy_image_url'),
            },
            'fabrics': {
                'title': data.get('fabrics_title'),
                'content': data.get('fabrics_content'),
                'image': data.get('fabrics_image'),
                'image_url': data.get('fabrics_image_url'),
                'image_2': data.get('fabrics_image_2'),
                'image_2_url': data.get('fabrics_image_2_url'),
                'image_3': data.get('fabrics_image_3'),
                'image_3_url': data.get('fabrics_image_3_url'),
            },
            'process': {
                'title': data.get('process_title'),
                'description': data.get('process_description'),
                'items': data.get('process_items'),
            },
            'is_active': data.get('is_active'),
        }
        
        return Response(organized_data, status=status.HTTP_200_OK)
