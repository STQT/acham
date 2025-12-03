from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from acham.products.models import Product


class OrderStatus(models.TextChoices):
    DRAFT = "draft", _("Draft")
    PENDING_PAYMENT = "pending_payment", _("Pending payment")
    PAYMENT_FAILED = "payment_failed", _("Payment failed")
    PAYMENT_CONFIRMED = "payment_confirmed", _("Payment confirmed")
    FULFILLMENT = "fulfillment", _("Preparing order")
    READY_FOR_PICKUP = "ready_for_pickup", _("Ready for pickup")
    SHIPPED = "shipped", _("Shipped")
    DELIVERED = "delivered", _("Delivered")
    CANCELLED = "cancelled", _("Cancelled")
    RETURN_REQUESTED = "return_requested", _("Return requested")
    RETURNED = "returned", _("Returned")
    REFUNDED = "refunded", _("Refunded")


class Order(models.Model):
    """Customer order that can be synchronised with external CRM systems."""

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    number = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
        help_text=_("Human readable order number (e.g. ACH-10001)."),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=32,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING_PAYMENT,
    )
    status_label = models.CharField(
        max_length=128,
        blank=True,
        help_text=_("Optional CRM-provided status label."),
    )
    currency = models.CharField(max_length=3, default="USD")
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total_items = models.PositiveIntegerField(default=0)

    payment_method = models.CharField(max_length=64, blank=True)
    shipping_method = models.CharField(max_length=64, blank=True)

    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=64, blank=True)

    external_id = models.CharField(
        max_length=128,
        blank=True,
        help_text=_("Identifier of the order in an external CRM or ERP."),
    )
    external_payload = models.JSONField(
        blank=True,
        null=True,
        help_text=_("Raw payload received from or sent to the CRM."),
    )

    notes = models.TextField(blank=True)

    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    fulfilled_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    expected_delivery = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ("-placed_at", "-id")
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"Order {self.number}"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        if self.total_items == 0:
            self.total_items = sum(item.quantity for item in self.items.all()) if self.pk else 0
        super().save(*args, **kwargs)

    @staticmethod
    def generate_number() -> str:
        ts = timezone.now().strftime("%Y%m%d%H%M%S")
        return f"ACH-{ts}-{uuid.uuid4().hex[:4].upper()}"

    def recalculate_totals(self, *, save: bool = True) -> None:
        subtotal = Decimal("0")
        total_items = 0
        for item in self.items.all():
            subtotal += item.total_price
            total_items += item.quantity

        self.subtotal_amount = subtotal
        self.total_items = total_items
        self.total_amount = subtotal - self.discount_amount + self.shipping_amount
        if save:
            self.save(update_fields=[
                "subtotal_amount",
                "total_items",
                "total_amount",
                "updated_at",
            ])


class OrderAddress(models.Model):
    class AddressType(models.TextChoices):
        BILLING = "billing", _("Billing")
        SHIPPING = "shipping", _("Shipping")

    order = models.ForeignKey(Order, related_name="addresses", on_delete=models.CASCADE)
    address_type = models.CharField(max_length=16, choices=AddressType.choices)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=64, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = _("Order address")
        verbose_name_plural = _("Order addresses")
        constraints = [
            models.UniqueConstraint(
                fields=("order", "address_type"),
                name="unique_order_address_type",
            )
        ]

    def __str__(self) -> str:  # pragma: no cover
        label = self.get_address_type_display()
        return f"{label} address for {self.order.number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product,
        related_name="order_items",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=64, blank=True)
    product_type = models.CharField(max_length=64, blank=True)
    color = models.CharField(max_length=64, blank=True)
    size = models.CharField(max_length=64, blank=True)
    preview_image = models.URLField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = _("Order item")
        verbose_name_plural = _("Order items")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.product_name} x{self.quantity}"

    def save(self, *args, **kwargs):
        if self.unit_price and not self.total_price:
            self.total_price = (self.unit_price or Decimal("0")) * self.quantity
        super().save(*args, **kwargs)
        if self.order_id:
            self.order.recalculate_totals(save=True)


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, related_name="status_history", on_delete=models.CASCADE)
    from_status = models.CharField(max_length=32, choices=OrderStatus.choices, blank=True)
    to_status = models.CharField(max_length=32, choices=OrderStatus.choices)
    note = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(blank=True, null=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_status_updates",
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Order status history")
        verbose_name_plural = _("Order status history")
        ordering = ("-changed_at",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.order.number}: {self.from_status} → {self.to_status}"


class PaymentTransactionStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    PREPARED = "prepared", _("Prepared")
    VERIFICATION_REQUIRED = "verification_required", _("Verification required")
    PROCESSING = "processing", _("Processing")
    SUCCESS = "success", _("Success")
    FAILED = "failed", _("Failed")
    CANCELLED = "cancelled", _("Cancelled")


class PaymentTransaction(models.Model):
    """Payment transaction for OCTO payment gateway."""

    order = models.ForeignKey(
        Order,
        related_name="payment_transactions",
        on_delete=models.CASCADE,
    )
    shop_transaction_id = models.CharField(
        max_length=128,
        unique=True,
        help_text=_("Unique transaction ID on our side (shop_transaction_id)."),
    )
    octo_transaction_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text=_("Transaction ID from OCTO (id from prepare_payment response)."),
    )
    octo_payment_id = models.CharField(
        max_length=128,
        blank=True,
        help_text=_("Payment ID from OCTO (id from verificationInfo response)."),
    )
    status = models.CharField(
        max_length=32,
        choices=PaymentTransactionStatus.choices,
        default=PaymentTransactionStatus.PENDING,
    )
    payment_method = models.CharField(
        max_length=32,
        blank=True,
        help_text=_("Payment method: bank_card, uzcard, humo"),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=_("Transaction amount in UZS."),
    )
    currency = models.CharField(max_length=3, default="UZS")
    request_payload = models.JSONField(
        blank=True,
        null=True,
        help_text=_("Request payload sent to OCTO."),
    )
    response_payload = models.JSONField(
        blank=True,
        null=True,
        help_text=_("Response payload received from OCTO."),
    )
    error_code = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Error code from OCTO if transaction failed."),
    )
    error_message = models.CharField(
        max_length=512,
        blank=True,
        help_text=_("Error message from OCTO if transaction failed."),
    )
    verification_url = models.URLField(
        blank=True,
        help_text=_("URL for OTP verification form (for Visa/MC)."),
    )
    seconds_left = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Seconds left for OTP verification."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Payment transaction")
        verbose_name_plural = _("Payment transactions")
        indexes = [
            models.Index(fields=["shop_transaction_id"]),
            models.Index(fields=["octo_transaction_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"Payment {self.shop_transaction_id} for {self.order.number}"
