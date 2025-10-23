from rest_framework import generics
from drf_spectacular.utils import extend_schema

from ..models import Banner, FAQ
from .serializers import BannerSerializer, FAQSerializer


@extend_schema(
    tags=['Banners'],
    summary="List all banners",
    description="Retrieve a list of all available banners."
)
class BannerListView(generics.ListAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer


@extend_schema(
    tags=['Banners'],
    summary="Retrieve banner details",
    description="Retrieve detailed information about a specific banner by ID."
)
class BannerDetailView(generics.RetrieveAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer


@extend_schema(
    tags=['FAQs'],
    summary="List all FAQs",
    description="Retrieve a list of all frequently asked questions."
)
class FAQListView(generics.ListAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer


@extend_schema(
    tags=['FAQs'],
    summary="Retrieve FAQ details",
    description="Retrieve detailed information about a specific FAQ by ID."
)
class FAQDetailView(generics.RetrieveAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer


# Create your views here.
