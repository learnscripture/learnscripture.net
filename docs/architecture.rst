==================================
 System services and architecture
==================================

This is a fairly standard Django app:

* nginx as front end web server, serves static files and delegates the rest to uwsgi
* uwsgi for running the Django app
* postgres as database.
* celeryd for background tasks
* rabbitmq for task queue
* memcached for caching
* supervisord for managing app services (uwsgi, memcached, celeryd)

Server config
=============

Passwords and private server config is stored in secrets.json that is not in
source control.

Third-party services
====================

The following integrations are used:

* Sentry for error reporting and tracking - https://sentry.io/learnscripturenet/production/

* Mailgun for sending and receiving emails. Webhooks and routes (including
  bounce handling) are set up with the management command ``setup_mailgun``.
  This needs to be run whenever webhooks change::

    fab manage_py_command:setup_mailgun

* ESV API for getting ESV text. We obey the ESV license which requires
  us to cache only a limited number of verses in the local database.
  The presence of the whole text, however, is needed for the word
  suggestions feature.

  Also, the ESV API is used for searching the ESV.

  A new version of the ESV API is in the works, which will give access to newer
  versions of the ESV text. This would be tricky to integrate - people who
  have memorized the old version will not appreciate having to re-learn.
