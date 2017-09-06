from learnscripture.celery import app as celery_app  # NOQA

__all__ = ['celery_app', 'default_app_config']

default_app_config = 'learnscripture.apps.LearnscriptureConfig'
