
Deployment
==========

Deployment is done using fabric, typically::

    fab deploy

If multiple people are working on the project, a method for syncing secrets.json
(not in VCS) between developers needs to be found.

See other commands in fabfile.py for more options.

See `<architecture.rst>`_ and `<server_setup.rst>`_ for more info.
