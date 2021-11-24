from django.apps import AppConfig


class BibleversesConfig(AppConfig):
    name = "bibleverses"

    def ready(self):
        from . import hooks  # noqa: F401
