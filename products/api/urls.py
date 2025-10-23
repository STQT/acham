from django.urls import path
from . import views

app_name = 'products_api'

urlpatterns = [
    # Product endpoints
    path('', views.ProductListView.as_view(), name='product-list'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('<int:pk>/complete/', views.product_complete_details, name='product-complete-details'),
    path('search/', views.product_search, name='product-search'),
    path('types/', views.product_types, name='product-types'),
    path('sizes/', views.product_sizes, name='product-sizes'),
    
    # Product shot endpoints
    path('<int:product_id>/shots/', views.ProductShotListView.as_view(), name='product-shot-list'),
    path('<int:product_id>/shots/<int:pk>/', views.ProductShotDetailView.as_view(), name='product-shot-detail'),

    # Collection endpoints
    path('collections/', views.CollectionListView.as_view(), name='collection-list'),
    path('collections/<int:pk>/', views.CollectionDetailView.as_view(), name='collection-detail'),
    
    # Favorites endpoints
    path('favorites/', views.user_favorites, name='user-favorites'),
    path('favorites/manage/', views.UserFavoriteListCreateView.as_view(), name='favorite-list-create'),
    path('favorites/<int:pk>/', views.UserFavoriteDestroyView.as_view(), name='favorite-destroy'),
    path('<int:product_id>/favorite/', views.toggle_favorite, name='toggle-favorite'),
    
    # Share endpoints
    path('shares/', views.ProductShareCreateView.as_view(), name='share-create'),
    path('<int:product_id>/share-stats/', views.product_share_stats, name='share-stats'),
]
