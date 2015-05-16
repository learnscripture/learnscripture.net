README
======

This is the source code for http://learnscripture.net/

Since there have only ever been one developer on the project to date, this
repo doesn't contain nice instructions for setting the project up, but it
does contain all the source code including deployment scripts, and excluding
only a small file containing passwords.

Some notes to help understand the project are below.

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

Tests use a mixture of Selenium for front end and lower level unit tests, which
combine to give a reasonable level of coverage.

Many of the detailed lower-level tests are in the 'identity.py' tests, since
most business logic runs off Identity.


$ ./manage.py test learnscripture.tests

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
  - celeryd apps (custom app listening on port)
  - supervisord app (custom app listening on port)

- Some manual installation of software.
  - lessc binary, using node/npm

Due to shared hosting with no root access, custom installation was often
necessary, and chef/puppet would probably not provide easy shortcuts.

Most config for these apps is stored in ./config (ideally all should be there)

See fabfile.py for more details on some of these things.

New texts and catechisms
========================

* The text needs to be prepared and loaded into the database in the development
  environment. This involves creating a TextVersion record in the admin, and then adding:

  * For Bibles, Verse instances corresponding to every Verse in the KJV
    (including missing verses, which should be marked with missing=True).

    Set LOADING_VERSES = True in settings to stop suggestions being created while you are
    doing this.

  * For catechisms, QAPairs for each question.

    Create JSON file with a list of [number, question, answer]

    run: ``./manage.py load_catechism <slug> <json_filename>``

* ``./manage.py setup_bibleverse_suggestions`` needs to be run, passing
  in the version slug

* Test locally.

* Create new TextVersion on live site, make sure that it is not public.

* Copy JSON file to live server:

  rsync ../texts/NCC.json cciw@learnscripture.net:/home/cciw

* Load JSON file into live site

  ssh cciw@learnscripture.net
  cd ~/webapps/learnscripture_django/src
  . ../venv/bin/activate
  ./manage.py load_catechism NCC ~/NCC.json

* Dump the word suggestions and transfer to the server.

  e.g.:

  psql -U learnscripture -d learnscripture_wordsuggestions -c "\\copy (select version_slug, reference, hash, suggestions from bibleverses_wordsuggestiondata where version_slug = 'NCC') TO stdout WITH CSV HEADER;" > wsd_NCC.csv

  rsync wsd_NCC.csv cciw@learnscripture.net:/home/cciw

* Load the word suggestions on the server, making sure to load them
  into the right databases.

  psql -U cciw_learnscripture -d learnscripture_wordsuggestions -c "\\copy bibleverses_wordsuggestiondata (version_slug, reference, hash, suggestions) from stdin CSV HEADER" < ~/wsd_NCC.csv

* Mark the text as public via the admin
