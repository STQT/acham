from django.urls import path

app_name = 'products'

# Intentionally left empty to avoid duplicating API routes under /products/api/.
# All API endpoints are exposed under /api/products/ via config.api_router.
urlpatterns = []
