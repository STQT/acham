"""URL patterns for payment endpoints."""

from django.urls import path

from acham.orders.api.payment_views import payment_notify

app_name = "payments"

urlpatterns = [
    path("notify/", payment_notify, name="payment-notify"),
]

