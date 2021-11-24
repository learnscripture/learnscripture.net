from django.apps import AppConfig


class LearnscriptureConfig(AppConfig):
    name = "learnscripture"
    verbose_name = "LearnScripture project"

    def ready(self):
        from . import hooks  # noqa: F401
