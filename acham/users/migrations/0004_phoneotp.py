from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_user_phone_unique"),
    ]

    operations = [
        migrations.CreateModel(
            name="PhoneOTP",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(max_length=20, verbose_name="phone number")),
                (
                    "purpose",
                    models.CharField(
                        choices=[("registration", "Registration"), ("login", "Login")],
                        max_length=32,
                        verbose_name="Purpose",
                    ),
                ),
                ("code_hash", models.CharField(max_length=128, verbose_name="OTP hash")),
                ("expires_at", models.DateTimeField(verbose_name="Expires at")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created at")),
                ("verified_at", models.DateTimeField(blank=True, null=True, verbose_name="Verified at")),
                ("attempts", models.PositiveSmallIntegerField(default=0, verbose_name="Attempts")),
                ("is_active", models.BooleanField(default=True, verbose_name="Is active")),
            ],
            options={
                "verbose_name": "Phone OTP",
                "verbose_name_plural": "Phone OTPs",
            },
        ),
        migrations.AddIndex(
            model_name="phoneotp",
            index=models.Index(fields=["phone", "purpose", "is_active"], name="users_phone_phone_pu_f2d8c3_idx"),
        ),
        migrations.AddIndex(
            model_name="phoneotp",
            index=models.Index(fields=["expires_at"], name="users_phone_expires_1d7468_idx"),
        ),
    ]

