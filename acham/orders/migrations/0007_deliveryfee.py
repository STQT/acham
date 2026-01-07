# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_currencyrate'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryFee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency', models.CharField(
                    choices=[('USD', 'USD'), ('UZS', 'UZS')],
                    default='USD',
                    help_text='Currency for which this delivery fee applies',
                    max_length=3,
                    unique=True,
                    verbose_name='Currency'
                )),
                ('amount', models.DecimalField(
                    decimal_places=2,
                    help_text='Fixed delivery fee amount in the specified currency',
                    max_digits=12,
                    verbose_name='Delivery Fee Amount'
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='Whether this delivery fee is currently active',
                    verbose_name='Is Active'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Delivery Fee',
                'verbose_name_plural': 'Delivery Fees',
                'ordering': ['currency'],
            },
        ),
    ]

