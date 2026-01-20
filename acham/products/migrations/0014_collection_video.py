# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_cart_shipment_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='video',
            field=models.FileField(
                blank=True,
                help_text='Video file for the collection (optional)',
                null=True,
                upload_to='collections/videos/',
                verbose_name='Video'
            ),
        ),
    ]
