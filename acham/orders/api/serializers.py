from __future__ import annotations

from decimal import Decimal
from typing import List

from django.db import transaction
from rest_framework import serializers

from acham.orders.models import (
    Order,
    OrderAddress,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
)
from acham.products.models import Cart


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = (
            "id",
            "from_status",
            "to_status",
            "note",
            "metadata",
            "changed_by",
            "changed_at",
        )


class OrderAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderAddress
        fields = (
            "id",
            "address_type",
            "first_name",
            "last_name",
            "email",
            "phone",
            "country",
            "city",
            "region",
            "postal_code",
            "address_line1",
            "address_line2",
            "company",
        )


class OrderItemSerializer(serializers.ModelSerializer):
    preview_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product",
            "product_name",
            "product_sku",
            "product_type",
            "color",
            "size",
            "preview_image",
            "unit_price",
            "quantity",
            "total_price",
            "metadata",
        )

    @staticmethod
    def resolve_preview_image(obj: OrderItem) -> str | None:
        if obj.preview_image:
            return obj.preview_image
        if obj.product:
            primary_shot = obj.product.shots.filter(is_primary=True).first()
            if primary_shot and primary_shot.image:
                return primary_shot.image.url
            fallback_shot = obj.product.shots.first()
            if fallback_shot and fallback_shot.image:
                return fallback_shot.image.url
        return None

    def get_preview_image(self, obj: OrderItem) -> str | None:
        return self.resolve_preview_image(obj)


class OrderSummarySerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()
    preview_images = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "public_id",
            "number",
            "status",
            "status_display",
            "status_label",
            "currency",
            "total_amount",
            "total_items",
            "expected_delivery",
            "placed_at",
            "updated_at",
            "preview_images",
        )

    def get_status_display(self, obj: Order) -> str:
        return obj.status_label or obj.get_status_display()

    def get_preview_images(self, obj: Order) -> List[str]:
        images: List[str] = []
        for item in obj.items.all():
            image = OrderItemSerializer.resolve_preview_image(item)
            if image:
                images.append(image)
            if len(images) >= 4:
                break
        return images


class OrderDetailSerializer(OrderSummarySerializer):
    items = OrderItemSerializer(many=True)
    addresses = OrderAddressSerializer(many=True)
    status_history = OrderStatusHistorySerializer(many=True)

    class Meta(OrderSummarySerializer.Meta):
        fields = OrderSummarySerializer.Meta.fields + (
            "subtotal_amount",
            "shipping_amount",
            "discount_amount",
            "payment_method",
            "shipping_method",
            "customer_email",
            "customer_phone",
            "notes",
            "external_id",
            "external_payload",
            "items",
            "addresses",
            "status_history",
        )


class OrderAddressInputSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=64)
    country = serializers.CharField(required=False, allow_blank=True, max_length=100)
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    region = serializers.CharField(required=False, allow_blank=True, max_length=100)
    postal_code = serializers.CharField(required=False, allow_blank=True, max_length=20)
    address_line1 = serializers.CharField(required=False, allow_blank=True, max_length=255)
    address_line2 = serializers.CharField(required=False, allow_blank=True, max_length=255)
    company = serializers.CharField(required=False, allow_blank=True, max_length=255)


class OrderCreateSerializer(serializers.Serializer):
    payment_method = serializers.CharField(max_length=64, required=False, allow_blank=True)
    shipping_method = serializers.CharField(max_length=64, required=False, allow_blank=True)
    shipping_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=Decimal("0"))
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=Decimal("0"))
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(required=False, allow_blank=True, max_length=64)
    notes = serializers.CharField(required=False, allow_blank=True)
    shipping_address = OrderAddressInputSerializer(required=False)
    billing_address = OrderAddressInputSerializer(required=False)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        if not user.is_authenticated:
            raise serializers.ValidationError("Authentication required to place an order.")

        cart: Cart | None = getattr(user, "cart", None)
        if not cart or not cart.items.exists():
            raise serializers.ValidationError("Cart is empty.")

        attrs["cart"] = cart
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        cart: Cart = validated_data.pop("cart")
        shipping_address_data = validated_data.pop("shipping_address", None)
        billing_address_data = validated_data.pop("billing_address", None)
        shipping_amount = Decimal(validated_data.pop("shipping_amount", Decimal("0")))
        discount_amount = Decimal(validated_data.pop("discount_amount", Decimal("0")))

        subtotal = Decimal("0")
        total_items = 0

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                payment_method=validated_data.get("payment_method", ""),
                shipping_method=validated_data.get("shipping_method", ""),
                shipping_amount=shipping_amount,
                discount_amount=discount_amount,
                customer_email=(validated_data.get("customer_email") or user.email or ""),
                customer_phone=(validated_data.get("customer_phone") or getattr(user, "phone", "") or ""),
                notes=validated_data.get("notes", ""),
                status=OrderStatus.PENDING_PAYMENT,
            )

            items_queryset = cart.items.select_related("product").all()
            for item in items_queryset:
                product = item.product
                unit_price = Decimal(product.price)
                line_total = unit_price * item.quantity
                subtotal += line_total
                total_items += item.quantity

                preview = None
                primary_shot = product.shots.filter(is_primary=True).first()
                if primary_shot and getattr(primary_shot.image, "url", None):
                    preview = primary_shot.image.url
                elif (fallback_shot := product.shots.first()) and getattr(fallback_shot.image, "url", None):
                    preview = fallback_shot.image.url

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_sku=str(product.id),
                    product_type=product.type,
                    color=product.color,
                    size=product.size,
                    preview_image=preview,
                    unit_price=unit_price,
                    quantity=item.quantity,
                    total_price=line_total,
                )

            order.subtotal_amount = subtotal
            order.total_items = total_items
            order.total_amount = subtotal - discount_amount + shipping_amount
            order.save(update_fields=[
                "subtotal_amount",
                "total_items",
                "total_amount",
                "shipping_amount",
                "discount_amount",
                "customer_email",
                "customer_phone",
                "payment_method",
                "shipping_method",
                "notes",
                "status",
                "updated_at",
            ])

            if shipping_address_data:
                OrderAddress.objects.update_or_create(
                    order=order,
                    address_type=OrderAddress.AddressType.SHIPPING,
                    defaults=shipping_address_data,
                )

            if billing_address_data:
                OrderAddress.objects.update_or_create(
                    order=order,
                    address_type=OrderAddress.AddressType.BILLING,
                    defaults=billing_address_data,
                )

            OrderStatusHistory.objects.create(
                order=order,
                from_status="",
                to_status=order.status,
                note="Order created",
            )

            cart.items.all().delete()

        return order
