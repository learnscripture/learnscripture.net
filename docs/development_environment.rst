Development environment
=======================

Normal development is done using the Django development server::

  ./manage.py runserver

You will also need to have ``webpack`` running with ``--watch``, which
has already been set up as an ``npm`` script::

  npm run watch

You can also do::

  npm run devserver

The former run ``webpack --watch`` to build Javascript bundles and watch for
changes. The latter uses ``webpack-dev-server``, and has hot reloading enabled
so that you don't have to press F5 manually, but is currently a bit buggy
(breaks font-awesome icons somehow?!?)


Celery
------

In development, Celery tasks are run with ``CELERY_ALWAYS_EAGER = True``. This
makes it easier to spot bugs that are introduced in background tasks, because
they don't happen in the background. No Celery process is needed to run the
tasks.

If you want to run a real Celery process, set ``CELERY_ALWAYS_EAGER = False``
and run something like::


  celery worker -A learnscripture.celery:app


You will also need to setup rabbitmq-server locally to do this. See
``fabfile.py`` for details.
