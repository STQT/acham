import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_alter_user_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name="email address"),
        ),
        migrations.AlterField(
            model_name="user",
            name="phone",
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Enter a valid international phone number starting with country code.",
                        regex="^\\+?[1-9]\\d{7,14}$",
                    )
                ],
                verbose_name="phone number",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(("email__isnull", False)),
                fields=("email",),
                name="users_unique_email",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(("phone__isnull", False)),
                fields=("phone",),
                name="users_unique_phone",
            ),
        ),
    ]

