# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0012_product_price_uzs_alter_product_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='shipment_amount',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Fixed shipping/delivery fee amount',
                max_digits=12,
                verbose_name='Shipment Amount'
            ),
        ),
    ]

