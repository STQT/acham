from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'acham.products'
    verbose_name = 'Products'

    def ready(self):
        try:
            import acham.products.translation  # noqa: F401
        except ImportError:
            pass
