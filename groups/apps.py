from django.apps import AppConfig


class GroupsConfig(AppConfig):
    name = "groups"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import hooks  # noqa: F401
