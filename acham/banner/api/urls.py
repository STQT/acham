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
    
    # Return request endpoint
    path('return-request/', views.ReturnRequestCreateView.as_view(), name='return-request-create'),
    
    # Email subscription endpoint
    path('subscribe/', views.EmailSubscriptionCreateView.as_view(), name='email-subscription-create'),
    
    # About page endpoints
    path('about/', views.AboutPageView.as_view(), name='about-page'),
    path('about/sections/', views.AboutPageSectionListView.as_view(), name='about-sections-list'),
    path('about/sections/<str:section_type>/', views.AboutPageSectionByTypeView.as_view(), name='about-section-by-type'),
]