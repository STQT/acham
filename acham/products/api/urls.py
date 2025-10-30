from django.urls import path
from .views import *

# app_name removed to prevent namespace collision

urlpatterns = [
    # 🛍️ PRODUCT MANAGEMENT (Lean)
    path('', ProductListView.as_view(), name='product-list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),

    # 🖼️ PRODUCT SHOTS
    path('<int:product_id>/shots/', ProductShotListView.as_view(), name='product-shot-list'),
    path('<int:product_id>/shots/<int:pk>/', ProductShotDetailView.as_view(), name='product-shot-detail'),

    # 📦 COLLECTIONS
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('collections/<int:pk>/', CollectionDetailView.as_view(), name='collection-detail'),
    path('collections/<int:collection_id>/products/', CollectionProductsView.as_view(), name='collection-products'),

    # 🆕 NEW ARRIVALS (Lean)
    path('new-arrivals/', NewArrivalsListView.as_view(), name='new-arrivals-list'),

    # ❤️ FAVORITES
    path('favorites/', user_favorites, name='user-favorites'),
    path('favorites/manage/', UserFavoriteListCreateView.as_view(), name='favorite-list-create'),
    path('favorites/<int:pk>/', UserFavoriteDestroyView.as_view(), name='favorite-destroy'),
    path('<int:product_id>/favorite/', toggle_favorite, name='toggle-favorite'),

    # 📤 SHARING
    path('shares/', ProductShareCreateView.as_view(), name='share-create'),
    path('<int:product_id>/share-stats/', product_share_stats, name='share-stats'),

    # 🛒 CART
    path('cart/', CartDetailView.as_view(), name='cart-detail'),
    path('cart/summary/', CartSummaryView.as_view(), name='cart-summary'),
    path('cart/items/', CartItemListCreateView.as_view(), name='cart-item-list-create'),
    path('cart/items/<int:pk>/', CartItemDetailView.as_view(), name='cart-item-detail'),
    path('cart/clear/', clear_cart, name='clear-cart'),

    # 🔗 RECOMMENDATIONS
    path('<int:product_id>/complete-the-look/', complete_the_look, name='complete-the-look'),
    path('<int:product_id>/recommendations/', product_recommendations, name='product-recommendations'),
]
