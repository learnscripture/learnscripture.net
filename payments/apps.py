from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    name = "payments"

    def ready(self):
        from . import hooks  # noqa: F401
