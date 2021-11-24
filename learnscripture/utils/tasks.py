# Facade for task class.
#
# This allows us to add our own logic, and switch between different
# actual task queue implementations more easiy.
#
# The current methods were named to allow us to easily switch from Celery
import django_ftl
from django.conf import settings
from django_q.tasks import async_task


def task(func):
    # This decorator returns the same function object as passed in, but with
    # methods attached. The seems the easiest way to satisfy the way django-q
    # expects to pickle/unpickle function objects.

    if settings.TASKS_EAGER:

        def apply_async(args):
            # Run tasks synchronously, in the same process,
            # and without any error catching - errors propagate
            # into main process, for easier debugging and
            # much better error visibility.

            # This has the disadvantage that we are running the code in a
            # significantly different environment, and especially without
            # request isolation. So we add some things here try to improve
            # isolation from main web request.

            # Simulate not having django_ftl.activate()
            with django_ftl.override(None):
                func(*args)

    else:

        def apply_async(args):
            async_task(func, *args)

    func.apply_async = apply_async

    return func
