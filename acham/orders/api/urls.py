from django.urls import path

from acham.orders.api.views import OrderDetailView, OrderListView, OrderStatusListView


urlpatterns = [
    path("", OrderListView.as_view(), name="order-list"),
    path("statuses/", OrderStatusListView.as_view(), name="order-statuses"),
    path("<uuid:order_id>/", OrderDetailView.as_view(), name="order-detail"),
]
