from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    name = "payments"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import hooks  # noqa: F401
