from django.urls import path
from . import views

app_name = 'banner_api'

urlpatterns = [
    path('', views.BannerListView.as_view(), name='banner-list'),
    path('<int:pk>/', views.BannerDetailView.as_view(), name='banner-detail'),


    # FAQ endpoints
    path('faq/', views.FAQListView.as_view(), name='faq-list'),
    path('faq/<int:pk>/', views.FAQDetailView.as_view(), name='faq-detail'),
    
    # Static pages endpoints
    path('pages/', views.StaticPageListView.as_view(), name='static-page-list'),
    path('pages/<str:page_type>/', views.StaticPageByTypeView.as_view(), name='static-page-by-type'),
]