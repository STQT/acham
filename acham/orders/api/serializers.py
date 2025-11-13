from __future__ import annotations

from typing import List

from rest_framework import serializers

from acham.orders.models import (
    Order,
    OrderAddress,
    OrderItem,
    OrderStatusHistory,
)


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
