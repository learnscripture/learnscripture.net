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

Tests
=====

Tests use a mixture of Selenium for front end and lower level unit tests, which
combine to give a reasonable level of coverage.

Many of the detailed lower-level tests are in the 'identity.py' tests, since
most business logic runs off Identity.


Server config
=============

Passwords and private server config is stored in settings_priv.py that is not in
source control.
