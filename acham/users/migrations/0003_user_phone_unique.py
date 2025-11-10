from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_user_phone"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="phone",
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Enter a valid international phone number starting with country code.",
                        regex="^\\+?[1-9]\\d{7,14}$",
                    )
                ],
                verbose_name="phone number",
            ),
        ),
    ]

