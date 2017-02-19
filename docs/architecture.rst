==================================
 System services and architecture
==================================

This is a fairly standard Django app:

* nginx as front end web server, serves static files and delegates the rest to uwsgi
* uwsgi for running the Django app
* postgres as database.
* celeryd for background tasks
* memcached for caching
* supervisord for managing app services (uwsgi, memcached, celeryd)


Because we have minimal requirements for background tasks (e.g. we never care
about the task result), for simplicity celeryd is configured to use the
(inefficient) builtin Django broker i.e. tasks are stored in database, and
polled for. This is inefficient, but relieves us having to install a proper
message queue.

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

* Google Analytics for statistics. There are also some stats of our own which
  can be viewed at https://learnscripture.net/stats/?requests&full_accounts
  although this hasn't always been working.

* ESV API for getting ESV text. We obey the ESV license which requires
  us to cache only a limited number of verses in the local database.
  The presence of the whole text, however, is needed for the word
  suggestions feature.

  Also, the ESV API is used for searching the ESV.

  A new version of the ESV API is in the works, which will give access to newer
  versions of the ESV text. This would be tricky to integrate - people who
  have memorized the old version will not appreciate having to re-learn.
