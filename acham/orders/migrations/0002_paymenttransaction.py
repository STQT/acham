# Generated manually

import decimal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PaymentTransactionStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ],
            options={
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="PaymentTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "shop_transaction_id",
                    models.CharField(
                        help_text="Unique transaction ID on our side (shop_transaction_id).",
                        max_length=128,
                        unique=True,
                    ),
                ),
                (
                    "octo_transaction_id",
                    models.CharField(
                        blank=True,
                        help_text="Transaction ID from OCTO (id from prepare_payment response).",
                        max_length=128,
                    ),
                ),
                (
                    "octo_payment_id",
                    models.CharField(
                        blank=True,
                        help_text="Payment ID from OCTO (id from verificationInfo response).",
                        max_length=128,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("prepared", "Prepared"),
                            ("verification_required", "Verification required"),
                            ("processing", "Processing"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=32,
                    ),
                ),
                (
                    "payment_method",
                    models.CharField(
                        blank=True,
                        help_text="Payment method: bank_card, uzcard, humo",
                        max_length=32,
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Transaction amount in UZS.",
                        max_digits=12,
                    ),
                ),
                ("currency", models.CharField(default="UZS", max_length=3)),
                (
                    "request_payload",
                    models.JSONField(
                        blank=True,
                        help_text="Request payload sent to OCTO.",
                        null=True,
                    ),
                ),
                (
                    "response_payload",
                    models.JSONField(
                        blank=True,
                        help_text="Response payload received from OCTO.",
                        null=True,
                    ),
                ),
                (
                    "error_code",
                    models.IntegerField(
                        blank=True,
                        help_text="Error code from OCTO if transaction failed.",
                        null=True,
                    ),
                ),
                (
                    "error_message",
                    models.CharField(
                        blank=True,
                        help_text="Error message from OCTO if transaction failed.",
                        max_length=512,
                    ),
                ),
                (
                    "verification_url",
                    models.URLField(
                        blank=True,
                        help_text="URL for OTP verification form (for Visa/MC).",
                    ),
                ),
                (
                    "seconds_left",
                    models.IntegerField(
                        blank=True,
                        help_text="Seconds left for OTP verification.",
                        null=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payment_transactions",
                        to="orders.order",
                    ),
                ),
            ],
            options={
                "verbose_name": "Payment transaction",
                "verbose_name_plural": "Payment transactions",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="paymenttransaction",
            index=models.Index(fields=["shop_transaction_id"], name="orders_paym_shop_tr_abc123_idx"),
        ),
        migrations.AddIndex(
            model_name="paymenttransaction",
            index=models.Index(fields=["octo_transaction_id"], name="orders_paym_octo_tr_def456_idx"),
        ),
        migrations.AddIndex(
            model_name="paymenttransaction",
            index=models.Index(fields=["status"], name="orders_paym_status_ghi789_idx"),
        ),
    ]

