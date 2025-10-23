from django.shortcuts import render
from rest_framework import generics

from ..models import Banner
from .serializers import BannerSerializer

class BannerListView(generics.ListAPIView):
    """
    List all banners.
    """
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer


# Create your views here.
