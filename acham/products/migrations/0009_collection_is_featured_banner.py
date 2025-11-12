from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_productrelation'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='is_featured_banner',
            field=models.BooleanField(
                default=False,
                help_text='Mark this collection to appear as the main banner on the storefront',
                verbose_name='Featured Banner',
            ),
        ),
        migrations.AddConstraint(
            model_name='collection',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_featured_banner=True),
                fields=('is_featured_banner',),
                name='unique_featured_collection_banner',
            ),
        ),
    ]

