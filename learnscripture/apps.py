from django.apps import AppConfig


class LearnscriptureConfig(AppConfig):
    name = "learnscripture"
    verbose_name = "LearnScripture project"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import hooks  # noqa: F401
