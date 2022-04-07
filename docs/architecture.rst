==================================
 System services and architecture
==================================

This is a fairly standard Django app:

* nginx as front end web server, serves static files and delegates the rest to uwsgi
* uwsgi for running the Django app
* postgres as database.
* django-q for background tasks
* memcached for caching
* supervisord for managing app services (uwsgi, memcached, django-q)


Server-side vs client-side code
===============================

Most pages on the site use classic web architecture:

* server-side rendered HTML
* small amounts of javascript where needed to improve the experience.

In the past, javascript was mostly jQuery based. Now, we are using `htmx
<htmx.org>`_, and `trying to move more things to use that pattern
<https://gitlab.com/learnscripture/learnscripture.net/-/issues/182>`_.

Just one page uses SPA-style — the “Learn” page. But:
- it is the page where users spend most of their time
- it is very complex and demanding in terms of user interface.

It is currently implemented in Elm, but `we are looking to replace it
<https://gitlab.com/learnscripture/learnscripture.net/-/issues/181>`_.


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
