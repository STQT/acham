from django.urls import path
from . import views

app_name = 'banner_api'

urlpatterns = [
    # FAQ endpoints
    path('faq/', views.FAQListView.as_view(), name='faq-list'),
    path('faq/<int:pk>/', views.FAQDetailView.as_view(), name='faq-detail'),
    
    # Static pages endpoints
    path('pages/', views.StaticPageListView.as_view(), name='static-page-list'),
    path('pages/<str:page_type>/', views.StaticPageByTypeView.as_view(), name='static-page-by-type'),
    
    # Contact form endpoint
    path('contact/', views.ContactMessageCreateView.as_view(), name='contact-create'),
]