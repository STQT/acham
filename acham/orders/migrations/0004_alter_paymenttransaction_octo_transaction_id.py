# Generated manually to fix octo_transaction_id nullable

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_delete_paymenttransactionstatus_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymenttransaction',
            name='octo_transaction_id',
            field=models.CharField(
                blank=True,
                help_text='Transaction ID from OCTO (id from prepare_payment response).',
                max_length=128,
                null=True,
            ),
        ),
    ]
