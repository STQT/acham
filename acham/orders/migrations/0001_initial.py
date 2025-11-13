import decimal
import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("products", "0010_collection_name_en_collection_name_ru_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                (
                    "number",
                    models.CharField(
                        editable=False,
                        help_text="Human readable order number (e.g. ACH-10001).",
                        max_length=32,
                        unique=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("pending_payment", "Pending payment"),
                            ("payment_failed", "Payment failed"),
                            ("payment_confirmed", "Payment confirmed"),
                            ("fulfillment", "Preparing order"),
                            ("ready_for_pickup", "Ready for pickup"),
                            ("shipped", "Shipped"),
                            ("delivered", "Delivered"),
                            ("cancelled", "Cancelled"),
                            ("return_requested", "Return requested"),
                            ("returned", "Returned"),
                            ("refunded", "Refunded"),
                        ],
                        default="pending_payment",
                        max_length=32,
                    ),
                ),
                ("status_label", models.CharField(blank=True, help_text="Optional CRM-provided status label.", max_length=128)),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("subtotal_amount", models.DecimalField(decimal_places=2, default=decimal.Decimal("0"), max_digits=12)),
                ("shipping_amount", models.DecimalField(decimal_places=2, default=decimal.Decimal("0"), max_digits=12)),
                ("discount_amount", models.DecimalField(decimal_places=2, default=decimal.Decimal("0"), max_digits=12)),
                ("total_amount", models.DecimalField(decimal_places=2, default=decimal.Decimal("0"), max_digits=12)),
                ("total_items", models.PositiveIntegerField(default=0)),
                ("payment_method", models.CharField(blank=True, max_length=64)),
                ("shipping_method", models.CharField(blank=True, max_length=64)),
                ("customer_email", models.EmailField(blank=True, max_length=254)),
                ("customer_phone", models.CharField(blank=True, max_length=64)),
                (
                    "external_id",
                    models.CharField(
                        blank=True,
                        help_text="Identifier of the order in an external CRM or ERP.",
                        max_length=128,
                    ),
                ),
                ("external_payload", models.JSONField(blank=True, help_text="Raw payload received from or sent to the CRM.", null=True)),
                ("notes", models.TextField(blank=True)),
                ("placed_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("fulfilled_at", models.DateTimeField(blank=True, null=True)),
                ("shipped_at", models.DateTimeField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("expected_delivery", models.DateField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="orders", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "verbose_name": "Order",
                "verbose_name_plural": "Orders",
                "ordering": ("-placed_at", "-id"),
            },
        ),
        migrations.CreateModel(
            name="OrderAddress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "address_type",
                    models.CharField(
                        choices=[("billing", "Billing"), ("shipping", "Shipping")],
                        max_length=16,
                    ),
                ),
                ("first_name", models.CharField(blank=True, max_length=150)),
                ("last_name", models.CharField(blank=True, max_length=150)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=64)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("region", models.CharField(blank=True, max_length=100)),
                ("postal_code", models.CharField(blank=True, max_length=20)),
                ("address_line1", models.CharField(blank=True, max_length=255)),
                ("address_line2", models.CharField(blank=True, max_length=255)),
                ("company", models.CharField(blank=True, max_length=255)),
                ("order", models.ForeignKey(on_delete=models.CASCADE, related_name="addresses", to="orders.order")),
            ],
            options={
                "verbose_name": "Order address",
                "verbose_name_plural": "Order addresses",
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name", models.CharField(max_length=255)),
                ("product_sku", models.CharField(blank=True, max_length=64)),
                ("product_type", models.CharField(blank=True, max_length=64)),
                ("color", models.CharField(blank=True, max_length=64)),
                ("size", models.CharField(blank=True, max_length=64)),
                ("preview_image", models.URLField(blank=True)),
                ("unit_price", models.DecimalField(decimal_places=2, default=decimal.Decimal("0"), max_digits=10)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("total_price", models.DecimalField(decimal_places=2, default=decimal.Decimal("0"), max_digits=12)),
                ("metadata", models.JSONField(blank=True, null=True)),
                ("order", models.ForeignKey(on_delete=models.CASCADE, related_name="items", to="orders.order")),
                (
                    "product",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="order_items", to="products.product"),
                ),
            ],
            options={
                "verbose_name": "Order item",
                "verbose_name_plural": "Order items",
            },
        ),
        migrations.CreateModel(
            name="OrderStatusHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_status", models.CharField(blank=True, choices=[
                    ("draft", "Draft"),
                    ("pending_payment", "Pending payment"),
                    ("payment_failed", "Payment failed"),
                    ("payment_confirmed", "Payment confirmed"),
                    ("fulfillment", "Preparing order"),
                    ("ready_for_pickup", "Ready for pickup"),
                    ("shipped", "Shipped"),
                    ("delivered", "Delivered"),
                    ("cancelled", "Cancelled"),
                    ("return_requested", "Return requested"),
                    ("returned", "Returned"),
                    ("refunded", "Refunded"),
                ], max_length=32)),
                ("to_status", models.CharField(choices=[
                    ("draft", "Draft"),
                    ("pending_payment", "Pending payment"),
                    ("payment_failed", "Payment failed"),
                    ("payment_confirmed", "Payment confirmed"),
                    ("fulfillment", "Preparing order"),
                    ("ready_for_pickup", "Ready for pickup"),
                    ("shipped", "Shipped"),
                    ("delivered", "Delivered"),
                    ("cancelled", "Cancelled"),
                    ("return_requested", "Return requested"),
                    ("returned", "Returned"),
                    ("refunded", "Refunded"),
                ], max_length=32)),
                ("note", models.CharField(blank=True, max_length=255)),
                ("metadata", models.JSONField(blank=True, null=True)),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "changed_by",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="order_status_updates", to=settings.AUTH_USER_MODEL),
                ),
                ("order", models.ForeignKey(on_delete=models.CASCADE, related_name="status_history", to="orders.order")),
            ],
            options={
                "verbose_name": "Order status history",
                "verbose_name_plural": "Order status history",
                "ordering": ("-changed_at",),
            },
        ),
        migrations.AddConstraint(
            model_name="orderaddress",
            constraint=models.UniqueConstraint(fields=("order", "address_type"), name="unique_order_address_type"),
        ),
    ]
