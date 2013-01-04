README
======

TODO



Business logic
==============

As usual with Django apps, there is debate about where best to put business
logic. Since this is a relatively small app, most business logic has been put
onto Models, which attempt to encapsulate a lot of the schema so that client
code can (roughly) obey the Law of Demeter

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

Tests use a mixture of Selenium for front end and lower level unit tests, which
combine to give a reasonable level of coverage.

Many of the detailed lower-level tests are in the 'identity.py' tests, since
most business logic runs off Identity.


$ ./manage.py test learnscripture


Server config
=============

Passwords and private server config is stored in secrets.json that is not in
source control.


Deployment
==========

Deployment is done using fabric, typically:

$  fab production deploy

Python dependencies are managed using requirements.txt, which is used
automatically in the deploy procedure.

Initial setup of the project was done using:

- WebFaction control panel to create apps
  - webserver apps (custom app listening on port)
  - rabbitmq apps (custom app listening on port)
  - celeryd apps (custom app listening on port)
  - pgbouncer app (custom app listening on port)
  - supervisord app (custom app listening on port)

- Some manual installation of software.
  - pgbouncer
  - lessc binary, using node/npm

- Some scripted installation of software, using fabric
  - rabbitmq

Due to shared hosting with no root access, custom installation was often
necessary, and chef/puppet would probably not provide easy shortcuts.

Most config for these apps is stored in ./config (ideally all should be there)

See fabfile.py for more details on some of these things.
