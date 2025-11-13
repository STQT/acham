from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from acham.orders.api.serializers import (
    OrderDetailSerializer,
    OrderSummarySerializer,
)
from acham.orders.models import Order, OrderStatus


class OrderQuerySetMixin:
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = (
            Order.objects.select_related("user")
            .prefetch_related(
                "items",
                "items__product__shots",
                "addresses",
                "status_history",
            )
            .order_by("-placed_at")
        )

        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)


class OrderListView(OrderQuerySetMixin, generics.ListAPIView):
    serializer_class = OrderSummarySerializer


class OrderDetailView(OrderQuerySetMixin, generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    lookup_field = "public_id"
    lookup_url_kwarg = "order_id"


class OrderStatusListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        statuses = [
            {
                "value": choice.value,
                "label": choice.label,
            }
            for choice in OrderStatus
        ]
        return Response(statuses)
