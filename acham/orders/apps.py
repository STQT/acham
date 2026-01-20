from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "acham.orders"
    verbose_name = _("Orders")

    def ready(self):
        """Import signals when the app is ready."""
        try:
            import acham.orders.signals  # noqa: F401
        except ImportError:
            pass
