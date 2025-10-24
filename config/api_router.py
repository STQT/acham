from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from acham.users.api.views import UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

# User Management
router.register("users", UserViewSet)

app_name = "api"
urlpatterns = router.urls + [
    # 🛍️ PRODUCT MANAGEMENT
    path("products/", include("products.api.urls")),
    
    # 🖼️ PRODUCT SHOTS
    path("product-shots/", include("products.api.urls")),
    
    # 📦 COLLECTIONS
    path("collections/", include("products.api.urls")),
    
    # 🆕 NEW ARRIVALS
    path("new-arrivals/", include("products.api.urls")),
    
    # ❤️ FAVORITES
    path("favorites/", include("products.api.urls")),
    
    # 📤 SHARING
    path("shares/", include("products.api.urls")),
    
    # 🛒 CART
    path("cart/", include("products.api.urls")),
    
    # 🔗 RECOMMENDATIONS
    path("recommendations/", include("products.api.urls")),
    
    # 🎯 BANNER
    path("banner/", include("banner.api.urls")),
]
