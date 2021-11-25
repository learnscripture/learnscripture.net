from django.apps import AppConfig


class EventsConfig(AppConfig):
    name = "events"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import hooks  # noqa: F401
