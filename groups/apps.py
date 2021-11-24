from django.apps import AppConfig


class GroupsConfig(AppConfig):
    name = "groups"

    def ready(self):
        from . import hooks  # noqa: F401
