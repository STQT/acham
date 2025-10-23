from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
class Banner(models.Model):
    """Homepage banner with optional video and image fallback."""

    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
        help_text=_("Administrative title for this banner"),
        blank=True
    )

    video = models.FileField(
        upload_to='banners/videos/',
        verbose_name=_("Video"),
        help_text=_("Banner video file (e.g., MP4, WebM)"),
        blank=True,
        null=True
    )

    image = models.ImageField(
        upload_to='banners/images/',
        verbose_name=_("Image Fallback"),
        help_text=_("Fallback image when video cannot be played"),
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether this banner is active on the homepage")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', '-created_at']
        verbose_name = _("Banner")
        verbose_name_plural = _("Banners")

    def __str__(self):
        label = self.title or str(self.pk)
        return f"Banner {label}"