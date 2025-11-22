from django.urls import path

from acham.orders.api.payment_views import (
    PaymentInitiateView,
    PaymentConfirmView,
    PaymentVerifyOTPView,
    PaymentStatusView,
    payment_notify_view,
)
from acham.orders.api.views import OrderDetailView, OrderListView, OrderStatusListView


urlpatterns = [
    path("", OrderListView.as_view(), name="order-list"),
    path("statuses/", OrderStatusListView.as_view(), name="order-statuses"),
    path("<uuid:order_id>/", OrderDetailView.as_view(), name="order-detail"),
    # Payment endpoints
    path("<uuid:order_id>/payment/initiate/", PaymentInitiateView.as_view(), name="payment-initiate"),
    path("<uuid:order_id>/payment/confirm/", PaymentConfirmView.as_view(), name="payment-confirm"),
    path("<uuid:order_id>/payment/verify-otp/", PaymentVerifyOTPView.as_view(), name="payment-verify-otp"),
    path("<uuid:order_id>/payment/status/", PaymentStatusView.as_view(), name="payment-status"),
]
