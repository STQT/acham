from django.conf import settings
from django.urls import include, path

app_name = "api"
urlpatterns = [
    # 🛍️ PRODUCTS (All product-related endpoints under /api/products/)
    path("products/", include("acham.products.api.urls")),
    # 🎯 BANNER
    path("banner/", include("acham.banner.api.urls")),
    # 👤 USERS (all user/api endpoints under /api/users/ by manual routes, no DRF router!)
    path("users/", include("acham.users.api.urls")),
]
