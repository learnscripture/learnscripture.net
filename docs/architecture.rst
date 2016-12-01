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
