from rest_framework import generics
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework import status

from ..models import FAQ, StaticPage, ContactMessage, ReturnRequest
from .serializers import FAQSerializer, StaticPageSerializer, ContactMessageSerializer, ReturnRequestSerializer


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


# Create your views here.
