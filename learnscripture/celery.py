from __future__ import absolute_import

import os
import logging

from celery import Celery
from celery.signals import task_failure

from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learnscripture.settings')


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


app = Celery('learnscripture')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
