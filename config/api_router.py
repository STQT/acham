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
    # 🛍️ PRODUCTS (All product-related endpoints under /api/products/)
    path("products/", include("products.api.urls")),
    
    # 🎯 BANNER
    path("banner/", include("banner.api.urls")),
]
