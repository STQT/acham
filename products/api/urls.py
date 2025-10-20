from django.urls import path
from . import views

app_name = 'products_api'

urlpatterns = [
    # Product endpoints
    path('', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('search/', views.product_search, name='product-search'),
    path('types/', views.product_types, name='product-types'),
    path('sizes/', views.product_sizes, name='product-sizes'),
    
    # Product shot endpoints
    path('<int:product_id>/shots/', views.ProductShotListCreateView.as_view(), name='product-shot-list-create'),
    path('<int:product_id>/shots/<int:pk>/', views.ProductShotDetailView.as_view(), name='product-shot-detail'),
]
