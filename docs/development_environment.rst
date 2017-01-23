Development environment
=======================

Celery
------

In development, Celery tasks are run with ``CELERY_ALWAYS_EAGER = True``. This
makes it easier to spot bugs that are introduced in background tasks, because
they don't happen in the background. No Celery process is needed to run the
tasks.

If you want to run a real Celery process, set ``CELERY_ALWAYS_EAGER = False``
and run something like::


  celery worker -A learnscripture.celery:app
