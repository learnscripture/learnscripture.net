
Development setup
=================

Since there has only ever been one developer on the project to date, these
instructions may not work completely, but they should be a start.

1. Create a directory 'learnscripture.net' and cd into it.

2. Checkout the sources from bitbucket into a folder called 'src'::

     hg clone ssh://hg@bitbucket.org/spookylukey/learnscripture.net src

3. Create a virtualenv for the project

4. Install dependencies.

   System dependencies:

   * postgresql 9.3 or later
   * memcached

   Python/virtualenv dependencies::

     pip install -r requirements.txt -r requirements-dev.txt
     nodeenv --node=system --python-virtualenv --requirement=requirements-node.txt

5. Create a postgres database matching the development one in
   ``learnscripture/settings.py``.

6. Create a file ``config/secrets.json`` containing just "{}" (proper contents
   are, well, secret). You will need a proper copy from the previous maintainer
   to deploy.

   If more than one developer is working on the project, and want to deploy
   directly, syncing this file will need to be rethought. It has been
   deliberately excluded from the project VCS repo to allow the source code to
   be published.

7. Setup database::

     ./manage.py migrate

   This may not work well - it might be best to get a snapshot of the real
   database to start from.

8. See if it works by doing::

     ./manage.py runserver

9. Then, try to run the tests::

     ./runtests.py
