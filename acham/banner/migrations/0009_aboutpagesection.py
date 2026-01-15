# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banner', '0008_emailsubscription_language'),
    ]

    operations = [
        migrations.CreateModel(
            name='AboutPageSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section_type', models.CharField(
                    choices=[
                        ('hero', 'Hero Section'),
                        ('history', 'History'),
                        ('philosophy', 'Philosophy'),
                        ('fabrics', 'Used Fabrics'),
                        ('process', 'Process and Cost')
                    ],
                    help_text='Type of section on the About page',
                    max_length=50,
                    unique=True,
                    verbose_name='Section Type'
                )),
                ('founder_name', models.CharField(
                    blank=True,
                    help_text='Name of the founder (for hero section)',
                    max_length=255,
                    verbose_name='Founder Name'
                )),
                ('founder_title', models.CharField(
                    blank=True,
                    help_text="Title/role of the founder (e.g., 'Founder of ACHAM')",
                    max_length=255,
                    verbose_name='Founder Title'
                )),
                ('hero_image', models.ImageField(
                    blank=True,
                    help_text='Hero section image (founder photo)',
                    null=True,
                    upload_to='about_page/',
                    verbose_name='Hero Image'
                )),
                ('title', models.CharField(
                    blank=True,
                    help_text='Section title',
                    max_length=255,
                    verbose_name='Title'
                )),
                ('content', models.TextField(
                    blank=True,
                    help_text='Section content text',
                    verbose_name='Content'
                )),
                ('image', models.ImageField(
                    blank=True,
                    help_text='Section image',
                    null=True,
                    upload_to='about_page/',
                    verbose_name='Image'
                )),
                ('image_2', models.ImageField(
                    blank=True,
                    help_text='Additional image (for fabrics section)',
                    null=True,
                    upload_to='about_page/',
                    verbose_name='Image 2'
                )),
                ('image_3', models.ImageField(
                    blank=True,
                    help_text='Additional image (for fabrics section)',
                    null=True,
                    upload_to='about_page/',
                    verbose_name='Image 3'
                )),
                ('process_description', models.TextField(
                    blank=True,
                    help_text='Description for process section',
                    verbose_name='Process Description'
                )),
                ('process_items', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='List of process items with icons and labels (JSON format)',
                    verbose_name='Process Items'
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='Whether this section is displayed',
                    verbose_name='Is Active'
                )),
                ('order', models.PositiveIntegerField(
                    default=0,
                    help_text='Display order on the page',
                    verbose_name='Order'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'About Page Section',
                'verbose_name_plural': 'About Page Sections',
                'ordering': ['order', 'section_type'],
            },
        ),
    ]

