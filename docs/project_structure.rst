===================
 Project structure
===================


Business logic
==============

As usual with Django apps, there is debate about where best to put business
logic. Since this is a relatively small app, most business logic has been put
onto Models, which attempt to encapsulate a lot of the schema so that client
code can (roughly) obey the Law of Demeter.

This means that a lot of business logic is driven off the Identity (which in
turn delegates to Account for some things). A middleware attaches identity to
the request object where it is available.

Views
=====

Although models are split between 'accounts', 'bibleverses', 'scores', and
'payments', views are mainly under learnscripture/views.py, because the views
almost always contain things from multiple apps.

hooks.py
========

In each app, hooks.py is used by that app to subscribe to events (usually in
other apps). It is usually imported from the bottom of the corresponding
models.py file.

signals.py
==========

This is where each app defines the signals that it sends. No logic for actually
sending this signal is contained here.

Often these signals can be simplified signals from other apps e.g. django's
post_save signals might be used to create a 'group_joined' signal which
abstracts over the fact that a group being joined corresponds to a Membership
object being created.


Tests
=====

Tests use a mixture of Selenium/WebTest for front end tests, and lower level
unit tests, which combine to give a reasonable level of coverage. We use
`django-functest <https://github.com/django-functest/django-functest/>`_, which
provides a higher level wrapper for both Selenium and WebTest. django-functest
was designed to make it easy to write two tests at once - one that runs against
Selenium, one against WebTest, but we rarely use this - tests are normally
either WebTest, for pages that don't use Javascript, or Selenium, for pages that
do. This is because the pages that do need Javascript can't usually gracefully
degrade in the case when Javascript is not available.

Many of the detailed lower-level tests are in the 'identity.py' tests, since
most business logic runs off Identity.

Run the tests::

  pytest

Exclude slow and flaky Selenium tests like this::

  pytest -m 'not selenium'

To see more options::

  pytest --help

Also `pytest docs <https://docs.pytest.org/en/latest/>`_ for more info.

* put "fsync = off" and "synchronous_commit = off" in your postgresql.conf
  for large speedups when running tests.
