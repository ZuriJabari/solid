from django.apps import AppConfig


class CheckoutConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'checkout'
    verbose_name = 'Checkout Management'

    def ready(self):
        import checkout.signals  # noqa
