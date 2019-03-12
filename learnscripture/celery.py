from __future__ import absolute_import

import logging
import os

import django_ftl
from celery import Celery
from celery.app.task import Task
from celery.signals import task_failure

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learnscripture.settings')
from django.conf import settings  # noqa isort:skip


@task_failure.connect
def log_exception(
        task_id=None,
        exception=None,
        args=None,
        kwargs=None,
        traceback=None,
        einfo=None,
        **other):
    from raven.contrib.django.raven_compat.handlers import SentryHandler
    logger = logging.getLogger("celery task exception")
    logger.addHandler(SentryHandler())
    logger.error(
        "celery task failure",
        exc_info=einfo.exc_info,
        extra={
            'task_id': task_id,
            'task_args': args,
            'task_kwargs': kwargs,
        }
    )


if settings.CELERY_TASK_ALWAYS_EAGER:
    # In production, this is False, which means that Celery tasks run in
    # separate process, and we must ensure that we activate a locale for
    # django_ftl. In dev/test, however, this is True (for easier debugging), but
    # it means that Celery tasks are run in-process and automatically inherit
    # the locale set up by the middleware as part of the request/response cycle.
    # This means that any failures to set a locale inside the task are hidden.
    # We fix that here:
    class MyTask(Task):
        def apply_async(self, *args, **kwargs):
            with django_ftl.override(None):
                return super(MyTask, self).apply_async(*args, **kwargs)

    app = Celery('learnscripture',
                 task_cls='learnscripture.celery.MyTask')
else:
    app = Celery('learnscripture')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
