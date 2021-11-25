from django.apps import AppConfig


class BibleversesConfig(AppConfig):
    name = "bibleverses"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import hooks  # noqa: F401
