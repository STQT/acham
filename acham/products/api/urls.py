from django.urls import path
from .views import *

# app_name removed to prevent namespace collision

urlpatterns = [
    # 🛍️ PRODUCT MANAGEMENT
    path('', ProductListView.as_view(), name='product-list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('<int:pk>/complete/', product_complete_details, name='product-complete-details'),
    path('search/', product_search, name='product-search'),
    path('types/', product_types, name='product-types'),
    path('sizes/', product_sizes, name='product-sizes'),
    
    # 🖼️ PRODUCT SHOTS
    path('<int:product_id>/shots/', ProductShotListView.as_view(), name='product-shot-list'),
    path('<int:product_id>/shots/<int:pk>/', ProductShotDetailView.as_view(), name='product-shot-detail'),

    # 📦 COLLECTIONS
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('collections/<int:pk>/', CollectionDetailView.as_view(), name='collection-detail'),
    path('collections/<int:collection_id>/products/', CollectionProductsView.as_view(), name='collection-products'),
    path('collections/<int:collection_id>/page/', collection_page, name='collection-page'),
    path('collections/search/', search_collections, name='search-collections'),
    
    # 🆕 NEW ARRIVALS
    path('new-arrivals/', NewArrivalsListView.as_view(), name='new-arrivals-list'),
    path('new-arrivals/collections/', new_arrivals_collections, name='new-arrivals-collections'),
    path('new-arrivals/page/', new_arrivals_page, name='new-arrivals-page'),
    
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
    path('<int:product_id>/add-to-cart/', add_to_cart, name='add-to-cart'),
    path('<int:product_id>/remove-from-cart/', remove_from_cart, name='remove-from-cart'),
    path('<int:product_id>/update-cart-quantity/', update_cart_item_quantity, name='update-cart-quantity'),
    
    # 🔗 RECOMMENDATIONS
    path('<int:product_id>/complete-the-look/', complete_the_look, name='complete-the-look'),
    path('<int:product_id>/recommendations/', product_recommendations, name='product-recommendations'),
]
