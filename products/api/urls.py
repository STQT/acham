from django.urls import path
from . import views

# app_name removed to prevent namespace collision

urlpatterns = [
    # 🛍️ PRODUCT MANAGEMENT
    path('', views.ProductListView.as_view(), name='product-list'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('<int:pk>/complete/', views.product_complete_details, name='product-complete-details'),
    path('search/', views.product_search, name='product-search'),
    path('types/', views.product_types, name='product-types'),
    path('sizes/', views.product_sizes, name='product-sizes'),
    
    # 🖼️ PRODUCT SHOTS
    path('<int:product_id>/shots/', views.ProductShotListView.as_view(), name='product-shot-list'),
    path('<int:product_id>/shots/<int:pk>/', views.ProductShotDetailView.as_view(), name='product-shot-detail'),

    # 📦 COLLECTIONS
    path('collections/', views.CollectionListView.as_view(), name='collection-list'),
    path('collections/<int:pk>/', views.CollectionDetailView.as_view(), name='collection-detail'),
    path('collections/<int:collection_id>/products/', views.CollectionProductsView.as_view(), name='collection-products'),
    path('collections/<int:collection_id>/page/', views.collection_page, name='collection-page'),
    path('collections/search/', views.search_collections, name='search-collections'),
    
    # 🆕 NEW ARRIVALS
    path('new-arrivals/', views.NewArrivalsListView.as_view(), name='new-arrivals-list'),
    path('new-arrivals/collections/', views.new_arrivals_collections, name='new-arrivals-collections'),
    path('new-arrivals/page/', views.new_arrivals_page, name='new-arrivals-page'),
    
    # ❤️ FAVORITES
    path('favorites/', views.user_favorites, name='user-favorites'),
    path('favorites/manage/', views.UserFavoriteListCreateView.as_view(), name='favorite-list-create'),
    path('favorites/<int:pk>/', views.UserFavoriteDestroyView.as_view(), name='favorite-destroy'),
    path('<int:product_id>/favorite/', views.toggle_favorite, name='toggle-favorite'),
    
    # 📤 SHARING
    path('shares/', views.ProductShareCreateView.as_view(), name='share-create'),
    path('<int:product_id>/share-stats/', views.product_share_stats, name='share-stats'),
    
    # 🛒 CART
    path('cart/', views.CartDetailView.as_view(), name='cart-detail'),
    path('cart/summary/', views.CartSummaryView.as_view(), name='cart-summary'),
    path('cart/items/', views.CartItemListCreateView.as_view(), name='cart-item-list-create'),
    path('cart/items/<int:pk>/', views.CartItemDetailView.as_view(), name='cart-item-detail'),
    path('cart/clear/', views.clear_cart, name='clear-cart'),
    path('<int:product_id>/add-to-cart/', views.add_to_cart, name='add-to-cart'),
    path('<int:product_id>/remove-from-cart/', views.remove_from_cart, name='remove-from-cart'),
    path('<int:product_id>/update-cart-quantity/', views.update_cart_item_quantity, name='update-cart-quantity'),
    
    # 🔗 RECOMMENDATIONS
    path('<int:product_id>/complete-the-look/', views.complete_the_look, name='complete-the-look'),
    path('<int:product_id>/recommendations/', views.product_recommendations, name='product-recommendations'),
]
