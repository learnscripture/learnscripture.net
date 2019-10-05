
Deployment
==========

Deployment is done using fabric, typically::

    fab deploy

Deployment is not currently safe for multiple people working on the project.
This could be fixed by:

2. Deploy using hg/VCS instead of rsync
3. As part of the deploy procedure, first do a push to a central repo (e.g.
   Gitlab). If this fails (due to conflict on the main branch, or creating
   new heads), then there are commits that the developer must merge first.

Also, a method for syncing secrets.json (not in VCS) between developers would
need to be found.

See other commands in fabfile.py for more options.

See architecture.rst and server_setup.rst for more info.

