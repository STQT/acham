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


class CurrencyRate(models.Model):
    """Model to store currency exchange rates from Central Bank of Uzbekistan."""
    
    code = models.CharField(
        max_length=3,
        unique=True,
        verbose_name=_("Currency Code"),
        help_text=_("ISO 4217 currency code (e.g., USD, EUR, RUB)")
    )
    rate = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name=_("Rate"),
        help_text=_("Exchange rate: 1 foreign currency = X UZS")
    )
    date = models.DateField(
        verbose_name=_("Date"),
        help_text=_("Date when this rate was effective")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', 'code']
        verbose_name = _("Currency Rate")
        verbose_name_plural = _("Currency Rates")
        indexes = [
            models.Index(fields=['code', '-date']),
            models.Index(fields=['-date']),
        ]
    
    def __str__(self) -> str:
        return f"{self.code} = {self.rate} UZS ({self.date})"
    
    @classmethod
    def get_latest_rate(cls, code: str) -> Decimal | None:
        """Get the latest exchange rate for a currency code."""
        try:
            rate_obj = cls.objects.get(code=code.upper())
            return Decimal(str(rate_obj.rate))
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_usd_rate(cls) -> Decimal:
        """Get the latest USD to UZS rate."""
        rate = cls.get_latest_rate('USD')
        if rate is None:
            # Fallback to default rate if not available
            return Decimal('12500')
        return rate


class DeliveryFee(models.Model):
    """Model for fixed delivery fee configuration."""
    
    currency = models.CharField(
        max_length=3,
        choices=[("USD", "USD"), ("UZS", "UZS")],
        default="USD",
        unique=True,
        verbose_name=_("Currency"),
        help_text=_("Currency for which this delivery fee applies"),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Delivery Fee Amount"),
        help_text=_("Fixed delivery fee amount in the specified currency"),
    )
    amount_uzs = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Delivery Fee Amount (UZS)"),
        help_text=_("Fixed delivery fee amount in Uzbekistani Som (UZS)"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this delivery fee is currently active"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Delivery Fee")
        verbose_name_plural = _("Delivery Fees")
        ordering = ["currency"]
    
    def __str__(self):
        if self.currency == "UZS" and self.amount_uzs:
            return f"Delivery Fee: {self.amount_uzs} {self.currency}"
        return f"Delivery Fee: {self.amount} {self.currency}"
    
    @classmethod
    def get_fee_for_currency(cls, currency: str) -> Decimal:
        """Get active delivery fee for a currency."""
        try:
            fee = cls.objects.get(currency=currency.upper(), is_active=True)
            # Если валюта UZS и есть amount_uzs, используем его
            if currency.upper() == "UZS" and fee.amount_uzs is not None:
                return Decimal(str(fee.amount_uzs))
            # Иначе используем amount
            return Decimal(str(fee.amount))
        except cls.DoesNotExist:
            # Return 0 if no fee configured
            return Decimal("0")


class PaymentTransaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "В ожидании"
        PREPARED = "PREPARED", "Подготовлено"
        VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED", "Требуется верификация"
        PROCESSING = "PROCESSING", "В обработке"
        SUCCESS = "SUCCESS", "Успешно"
        FAILED = "FAILED", "Неуспешно"
        CANCELLED = "CANCELLED", "Отменено"
        REFUNDED = "REFUNDED", "Возвращено"

    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="payment_transactions")
    shop_transaction_id = models.CharField(max_length=255, unique=True, db_index=True)
    octo_transaction_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    octo_payment_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="UZS")
    verification_url = models.URLField(max_length=500, blank=True, null=True)
    seconds_left = models.PositiveIntegerField(blank=True, null=True)
    error_code = models.CharField(max_length=100, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Octo Transaction {self.shop_transaction_id} for Order {self.order.public_id} - {self.status}"

    class Meta:
        verbose_name = _("Payment transaction")
        verbose_name_plural = _("Payment transactions")
