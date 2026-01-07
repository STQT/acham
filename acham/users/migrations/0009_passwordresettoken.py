# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_user_registration_method'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=64, unique=True, verbose_name='Token')),
                ('expires_at', models.DateTimeField(db_index=True, verbose_name='Expires at')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('used_at', models.DateTimeField(blank=True, null=True, verbose_name='Used at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='password_reset_tokens', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Password Reset Token',
                'verbose_name_plural': 'Password Reset Tokens',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='passwordresettoken',
            index=models.Index(fields=['token', 'is_active'], name='users_pass_token_9a8b2c_idx'),
        ),
        migrations.AddIndex(
            model_name='passwordresettoken',
            index=models.Index(fields=['expires_at'], name='users_pass_expires_7c3d4e_idx'),
        ),
        migrations.AddIndex(
            model_name='passwordresettoken',
            index=models.Index(fields=['user', 'is_active'], name='users_pass_user_id_5e6f7g_idx'),
        ),
    ]

