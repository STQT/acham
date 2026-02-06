from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    Order,
    OrderAddress,
    OrderItem,
    OrderStatusHistory,
    PaymentTransaction,
    CurrencyRate,
    DeliveryFee,
    OrderStatus,
)


class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity", "total_price", "preview_image_display", "preview_image")
    
    def preview_image_display(self, obj):
        """Отображает изображение товара вместо пути."""
        if obj.preview_image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover; border-radius: 4px;" />',
                obj.preview_image,
            )
        return "—"
    
    preview_image_display.short_description = _("Preview Image")


class OrderAddressInline(admin.StackedInline):
    model = OrderAddress
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "colored_status", "total_amount", "currency", "placed_at")
    list_filter = ("status", "currency", "placed_at")
    search_fields = ("number", "external_id", "customer_email", "customer_phone")
    inlines = (OrderItemInline, OrderAddressInline)
    ordering = ("-placed_at",)
    
    def colored_status(self, obj):
        """Отображает статус заказа с цветом."""
        status = obj.status
        status_display = obj.get_status_display()
        
        # Определяем цвет в зависимости от статуса
        if status in [
            OrderStatus.CANCELLED,
            OrderStatus.REFUNDED,
            OrderStatus.RETURNED,
            OrderStatus.PAYMENT_FAILED,
        ]:
            # Отклонен - красный
            color = "#D32F2F"
        elif status == OrderStatus.DELIVERED:
            # Успешно - зеленый
            color = "green"
        elif status == OrderStatus.FULFILLMENT:
            color = "#2196F3"
        elif status == OrderStatus.PENDING_PAYMENT:
            color = "#FFC107"
        elif status == OrderStatus.PAYMENT_CONFIRMED:
            color = "#2E7D32"
        else:
            # В процессе - желтый
            color = "yellow"
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status_display,
        )
    
    colored_status.short_description = _("Status")
    colored_status.admin_order_field = "status"
    fieldsets = (
        (_("Identification"), {"fields": ("number", "public_id", "external_id", "status", "status_label")}),
        (_("Ownership"), {"fields": ("user",)}),
        (_("Financial"), {
            "fields": (
                "currency",
                "subtotal_amount",
                "shipping_amount",
                "discount_amount",
                "total_amount",
                "total_items",
            )
        }),
        (_("Customer"), {"fields": ("customer_email", "customer_phone")}),
        (_("Logistics"), {
            "fields": (
                "payment_method",
                "shipping_method",
                "expected_delivery",
                "notes",
            )
        }),
        (_("Timeline"), {
            "fields": (
                "placed_at",
                "paid_at",
                "fulfilled_at",
                "shipped_at",
                "delivered_at",
                "cancelled_at",
            )
        }),
        (_("External data"), {"fields": ("external_payload",)}),
    )
    readonly_fields = (
        "number",
        "public_id",
        "placed_at",
        "updated_at",
        "paid_at",
        "fulfilled_at",
        "shipped_at",
        "delivered_at",
        "cancelled_at",
    )


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("order", "from_status", "to_status", "changed_by", "changed_at")
    list_filter = ("to_status", "changed_at")
    search_fields = ("order__number", "note")
    ordering = ("-changed_at",)


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "shop_transaction_id",
        "order",
        "status",
        "amount",
        "currency",
        "error_code",
        "error_message",
        "created_at",
        "completed_at",
    )
    list_filter = ("status", "currency", "created_at")
    search_fields = (
        "shop_transaction_id",
        "octo_transaction_id",
        "octo_payment_id",
        "order__number",
    )
    readonly_fields = (
        "shop_transaction_id",
        "octo_transaction_id",
        "octo_payment_id",
        "created_at",
        "updated_at",
        "completed_at",
        "request_payload",
        "response_payload",
    )
    ordering = ("-created_at",)
    fieldsets = (
        (_("Identification"), {
            "fields": (
                "order",
                "shop_transaction_id",
                "octo_transaction_id",
                "octo_payment_id",
            )
        }),
        (_("Status"), {
            "fields": (
                "status",
                "error_code",
                "error_message",
            )
        }),
        (_("Financial"), {
            "fields": (
                "amount",
                "currency",
            )
        }),
        (_("Verification"), {
            "fields": (
                "verification_url",
                "seconds_left",
            )
        }),
        (_("Timeline"), {
            "fields": (
                "created_at",
                "updated_at",
                "completed_at",
            )
        }),
        (_("Data"), {
            "fields": (
                "request_payload",
                "response_payload",
            ),
            "classes": ("collapse",            ),
        }),
    )


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ("code", "rate", "date", "created_at", "updated_at")
    list_filter = ("code", "date", "created_at")
    search_fields = ("code",)
    ordering = ("-date", "-code")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DeliveryFee)
class DeliveryFeeAdmin(admin.ModelAdmin):
    list_display = ("currency", "amount", "amount_uzs", "is_active", "created_at", "updated_at")
    list_filter = ("currency", "is_active", "created_at")
    search_fields = ("currency",)
    ordering = ("currency",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (_("Configuration"), {
            "fields": (
                "currency",
                "amount",
                "amount_uzs",
                "is_active",
            )
        }),
        (_("Timeline"), {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )
