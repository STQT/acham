# Generated migration for adding countries
from django.db import migrations

def create_countries(apps, schema_editor):
    Country = apps.get_model('users', 'Country')
    
    countries = [
        {'name': 'Uzbekistan', 'code': 'UZ', 'phone_code': '+998', 'requires_phone_verification': 'Y'},
        {'name': 'United States', 'code': 'US', 'phone_code': '+1', 'requires_phone_verification': 'N'},
        {'name': 'United Kingdom', 'code': 'GB', 'phone_code': '+44', 'requires_phone_verification': 'N'},
        {'name': 'Germany', 'code': 'DE', 'phone_code': '+49', 'requires_phone_verification': 'N'},
        {'name': 'France', 'code': 'FR', 'phone_code': '+33', 'requires_phone_verification': 'N'},
        {'name': 'Russia', 'code': 'RU', 'phone_code': '+7', 'requires_phone_verification': 'N'},
        {'name': 'Turkey', 'code': 'TR', 'phone_code': '+90', 'requires_phone_verification': 'N'},
        {'name': 'Kazakhstan', 'code': 'KZ', 'phone_code': '+7', 'requires_phone_verification': 'N'},
        {'name': 'Kyrgyzstan', 'code': 'KG', 'phone_code': '+996', 'requires_phone_verification': 'N'},
        {'name': 'Tajikistan', 'code': 'TJ', 'phone_code': '+992', 'requires_phone_verification': 'N'},
    ]
    
    for country_data in countries:
        Country.objects.get_or_create(
            code=country_data['code'],
            defaults=country_data
        )

def reverse_create_countries(apps, schema_editor):
    Country = apps.get_model('users', 'Country')
    Country.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_user_phone'),  # Adjust this to match your latest migration
    ]

    operations = [
        migrations.RunPython(create_countries, reverse_create_countries),
    ]
