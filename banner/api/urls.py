from django.urls import path
from . import views

app_name = 'banner_api'

urlpatterns = [
    path('', views.BannerListView.as_view(), name='banner-list'),
]