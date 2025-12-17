from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    Order,
    OrderAddress,
    OrderItem,
    OrderStatusHistory,
    PaymentTransaction,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity", "total_price")


class OrderAddressInline(admin.StackedInline):
    model = OrderAddress
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "total_amount", "currency", "placed_at")
    list_filter = ("status", "currency", "placed_at")
    search_fields = ("number", "external_id", "customer_email", "customer_phone")
    inlines = (OrderItemInline, OrderAddressInline)
    ordering = ("-placed_at",)
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
            "classes": ("collapse",),
        }),
    )
