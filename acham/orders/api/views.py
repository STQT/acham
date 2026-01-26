from __future__ import annotations

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from acham.orders.api.serializers import (
    OrderDetailSerializer,
    OrderSummarySerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    OrderEmailSubscriptionSerializer,
    OrderEmailSubscriptionUpdateSerializer,
)
from acham.orders.models import Order, OrderStatus


class OrderQuerySetMixin:
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = (
            Order.objects.select_related("user")
            .prefetch_related(
                "items__product",  # select_related для product через prefetch
                "items__product__shots",  # prefetch shots для оптимизации
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

    def get_serializer_context(self):
        """Add delivery fees to context to avoid N+1 queries."""
        context = super().get_serializer_context()
        
        # Загружаем DeliveryFee один раз для всех заказов
        from acham.orders.models import DeliveryFee
        delivery_fees = {}
        for fee in DeliveryFee.objects.filter(is_active=True):
            delivery_fees[fee.currency] = fee
        
        context["delivery_fees"] = delivery_fees
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        detail_serializer = OrderDetailSerializer(order, context=self.get_serializer_context())
        headers = self.get_success_headers(detail_serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class OrderDetailView(OrderQuerySetMixin, generics.RetrieveUpdateAPIView):
    serializer_class = OrderDetailSerializer
    lookup_field = "public_id"
    lookup_url_kwarg = "order_id"

    def get_serializer_class(self):
        if self.request.method.upper() in ["PUT", "PATCH"]:
            return OrderUpdateSerializer
        return super().get_serializer_class()

    def update(self, request, *args, **kwargs):
        """Override update to return full order details with public_id."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_order = serializer.save()

        # Return full order details using OrderDetailSerializer
        detail_serializer = OrderDetailSerializer(updated_order, context=self.get_serializer_context())
        return Response(detail_serializer.data)


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


class OrderEmailSubscriptionView(OrderQuerySetMixin, APIView):
    """Subscribe to order status updates via email."""
    
    permission_classes = (IsAuthenticated,)

    def _get_order(self, order_id):
        """Get order and check permissions."""
        try:
            order = Order.objects.get(public_id=order_id)
        except Order.DoesNotExist:
            return None, Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if user has access to this order
        if not self.request.user.is_staff and order.user != self.request.user:
            return None, Response(
                {"error": "You don't have permission to access this order"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return order, None

    def get(self, request, order_id, *args, **kwargs):
        """
        Get email subscription information for an order.
        
        GET /api/orders/{order_id}/subscribe-email/?country=Uzbekistan
        """
        order, error_response = self._get_order(order_id)
        if error_response:
            return error_response

        # Get country from query params (optional)
        country = request.query_params.get("country", "")

        # Check if subscribed (has customer_email)
        is_subscribed = bool(order.customer_email)
        
        response_data = {
            "is_subscribed": is_subscribed,
            "email": order.customer_email if is_subscribed else None,
            "order_number": order.number,
        }
        
        if country:
            response_data["country"] = country

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, order_id, *args, **kwargs):
        """
        Subscribe to order status updates.
        
        POST /api/orders/{order_id}/subscribe-email/?country=Uzbekistan
        Body: {
            "email": "user@example.com",
            "language": "ru"  # optional: uz, ru, en
        }
        """
        order, error_response = self._get_order(order_id)
        if error_response:
            return error_response

        # Get country from query params (optional)
        country = request.query_params.get("country", "")

        # Validate the email
        serializer = OrderEmailSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data["email"]
        language = serializer.validated_data.get("language", "ru")

        # Update order with customer email
        order.customer_email = email
        order.save(update_fields=["customer_email", "updated_at"])

        response_data = {
            "message": "Successfully subscribed to order status updates",
            "email": email,
            "language": language,
            "order_number": order.number,
            "is_subscribed": True,
        }
        
        if country:
            response_data["country"] = country

        return Response(response_data, status=status.HTTP_200_OK)

    def patch(self, request, order_id, *args, **kwargs):
        """
        Update email subscription for an order.
        
        PATCH /api/orders/{order_id}/subscribe-email/?country=Uzbekistan
        Body: {
            "email": "newuser@example.com",  # optional
            "language": "en"  # optional: uz, ru, en
        }
        """
        order, error_response = self._get_order(order_id)
        if error_response:
            return error_response

        # Get country from query params (optional)
        country = request.query_params.get("country", "")

        # Validate the data
        serializer = OrderEmailSubscriptionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update email if provided
        email = serializer.validated_data.get("email")
        if email:
            order.customer_email = email
            order.save(update_fields=["customer_email", "updated_at"])
        
        # Get current email (updated or existing)
        current_email = order.customer_email

        response_data = {
            "message": "Email subscription updated successfully",
            "email": current_email,
            "is_subscribed": bool(current_email),
            "order_number": order.number,
        }
        
        # Add language if provided
        language = serializer.validated_data.get("language")
        if language:
            response_data["language"] = language
        
        if country:
            response_data["country"] = country

        return Response(response_data, status=status.HTTP_200_OK)
