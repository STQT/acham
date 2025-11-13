from __future__ import annotations

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from acham.orders.api.serializers import (
    OrderDetailSerializer,
    OrderSummarySerializer,
    OrderCreateSerializer,
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


class OrderListView(OrderQuerySetMixin, generics.ListCreateAPIView):
    serializer_class = OrderSummarySerializer

    def get_serializer_class(self):
        if self.request.method.upper() == "POST":
            return OrderCreateSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        detail_serializer = OrderDetailSerializer(order, context=self.get_serializer_context())
        headers = self.get_success_headers(detail_serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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
