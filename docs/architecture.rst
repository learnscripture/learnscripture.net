==================================
 System services and architecture
==================================

This is a fairly standard `Django <https://www.djangoproject.com/>`_ app:

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
* small amounts of Javascript where needed to improve the experience.

In the past, Javascript was mostly jQuery based. Now, we are using `htmx
<htmx.org>`_, and `trying to move more things to use that pattern
<https://github.com/learnscripture/learnscripture.net/issues/182>`_.

Just one page uses SPA-style — the “Learn” page. But:
- it is the page where users spend most of their time
- it is very complex and demanding in terms of user interface.

It is currently implemented in Elm, but `we are looking to replace that
<https://github.com/learnscripture/learnscripture.net/issues/181>`_.


Server config
=============

Passwords and private server config is stored in secrets.json that is not in
source control.

Third-party services
====================

The following integrations are used:

* Sentry for error reporting and tracking - https://sentry.io/learnscripturenet/production/

* Mailgun for sending emails. We send very little email — only for password reset.
  We have set this up using Mailgun’s instructions, using the anymail package
  which supports mailgun.

* We do not handle inbound email in the website at all.

  To avoid the problems of a contact form that gets spammed, but has a “from”
  website@learnscripture.net address (making it hard to deal with and giving us
  a bad reputation), we don’t have a contact form, but instead require people to
  email contact@learnscripture.net (or other addresses).

  This email is received via fastmail.com on Luke’s personal email, following the
  instructions on fastmail.com for setting up domains to attach to a personal
  account.

  This means spammers have to use their own email systems for sending spam to
  @learnscripture.net addresses, which can be handled using normal spam controls.

  It also means that we don’t have to handle bounces in the website code,

* ESV API for getting ESV text. We obey the ESV license which requires
  us to cache only a limited number of verses in the local database.
  The presence of the whole text, however, is needed for the word
  suggestions feature.

  Also, the ESV API is used for searching the ESV.

  A new version of the ESV API is in the works, which will give access to newer
  versions of the ESV text. This would be tricky to integrate - people who
  have memorized the old version will not appreciate having to re-learn.
