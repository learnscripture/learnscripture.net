from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import hooks  # noqa: F401
