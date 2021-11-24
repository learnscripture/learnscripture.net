from django.apps import AppConfig


class CommentsConfig(AppConfig):
    name = "comments"

    def ready(self):
        from . import hooks  # noqa: F401
