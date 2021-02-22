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


django-q
--------

This is used for background tasks.

In development, these tasks are run eagerly i.e. synchronously, in the same
process. This makes it easier to spot bugs that are introduced in background
tasks, because they don't happen in the background. No worker process is needed
to run the tasks.

If you want to run a real worker process, set ``TASKS_EAGER = True`` in
``settings_local.py`` and run the django-q process like::


  ./manage.py qcluster


Use /task-queue-debug/ URL for debugging.

uwsgi
-----

In production we use uswgi as a server. For testing that locally you can do
something like::

  $ pip install uwsgi
  $ manage.py collectstatic
  $ uwsgi --home ~/.virtualenvs/learnscripture -w learnscripture.wsgi --master --process 4 --http :9090 --check-static ..

(see ../config/supervisor.conf.template for production command line)
