# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_deliveryfee'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryfee',
            name='amount_uzs',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Fixed delivery fee amount in Uzbekistani Som (UZS)',
                max_digits=12,
                null=True,
                verbose_name='Delivery Fee Amount (UZS)'
            ),
        ),
    ]

