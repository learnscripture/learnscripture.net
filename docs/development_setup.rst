
Development setup
=================

Since there has only ever been one developer on the project to date, these
instructions may not work completely, but they should be a start.

These instructions assume you are working in a Linux or Unix like environment
(Mac should work, or a Ubuntu 16.04 virtual machine), with Python 3.5 and Mercurial
installed.

1. Create a directory 'learnscripture.net' and cd into it.

2. Checkout the sources from bitbucket into a folder called 'src'.

   First, it is probably best to fork the project on bitbucket - https://bitbucket.org/learnscripture/learnscripture.net/fork

   Then clone your fork locally::

     hg clone ssh://hg@bitbucket.org/yourusename/learnscripture.net src

   You will also need a copy of the text sources, checked out in 'texts' in a sibling directory to 'src'::

     hg clone ssh://hg@bitbucket.org/learnscripture/learnscripture-texts texts

3. Create a virtualenv for the project e.g.::

     mkvirtualenv learnscripture --python=`which python3.5` -a `pwd`

4. Install dependencies.

   System dependencies:

   * postgresql 9.4 or later
   * memcached
   * rabbitmq-server
   * nodejs
   * npm

   Python/virtualenv dependencies: from inside the learnscripture.net/src/
   folder, do::

     pip install -r requirements.txt

   npm/javascript dependencies. First do::

     nodeenv --node=system --python-virtualenv

   Deactivate and re-activate the virtualenv for changes to take effect.

   Now we also need our node and Javascript deps::

     nodeenv --update -p --requirement=requirements-node.txt
     npm install

   We also need to install Elm dependencies::

     cd learnscripture/static/elm
     elm-install
     cd tests
     elm-install

5. Create postgres databases matching the development ones in
   ``learnscripture/settings.py``, both for ``learnscripture`` and
   ``learnscripture_wordsuggestions``.

   Similarly set up RabbitMQ::

     $ rabbitmqctl add_user learnscripture foo
     $ rabbitmqctl add_vhost learnscripture
     $ rabbitmqctl set_permissions -p learnscripture learnscripture ".*" ".*" ".*"

   You will also need to add 'learnscripture.local' as
   aliases for 127.0.0.1 in /etc/hosts

6. Create a file ``config/secrets.json`` containing at least the following:

       {"RABBITMQ_USERNAME": "learnscripture",
        "RABBITMQ_PASSWORD": "foo",
        "ESV_API_KEY": "IP"
       }

   (proper contents are, well, secret).
   You will need a proper copy from the previous maintainer to deploy.

   If you have access rights to the server, you can do::

       scp learnscripture@learnscripture.net:/home/learnscripture/webapps/learnscripture/versions/current/src/config/secrets.json config/secrets.json

   If more than one developer is working on the project, and want to deploy
   directly, syncing this file will need to be rethought. It has been
   deliberately excluded from the project VCS repo to allow the source code to
   be published.

7. Setup development database::

     ./manage.py migrate
     ./manage.py migrate --database wordsuggestions

   You will then need to load at least the NET Bible, as follows::

     ./manage.py load_text ../texts/db_dumps NET

   This assumes you are in the ``src`` directory, with the directory structure
   described above, so the ``texts`` directory is a sibling of ``src`` and
   contains the learnscripture-texts repo.

   You can add additional text names after ``NET`` above, but you need at
   least that one as it is the default Bible.

   An alternative to the above is to get a snapshot of production::

     $ fab get_and_load_production_db

8. See if it works by doing::

     ./manage.py runserver

   And, in separate terminals::

     fab run_ftl2elm:true
     npm run watch

   (These are long running processes that re-run themselves when files change)
   Browse the site on http://learnscripture.local:8001/

9. Then, try to run the tests::

     ./runtests.py

   See also :doc:`project_structure.rst` for more info on running tests.


Additional tasks
~~~~~~~~~~~~~~~~

These should be done at some point, but don't need to be done immediately.

10. For the 'on screen buttons' testing mode, you will need to set up the
    contents of the word suggestions database. Since this is a large amount of
    data, all of which is derived from the texts and other static content, it is
    in a separate database, and not downloaded as part of the text itself. To
    generate it, do::

      ./manage.py setup_bibleverse_suggestions NET

    (Other version names can be added at the end of that line)

    This will take a long time, and thrash your computer too... it's doing Markov
    chain analysis of various lengths on the whole Bible, plus other things, in
    order to generate sensible alternatives to the correct word when testing if
    the user knows what the next word is.

    The process can be interrupted with minimal loss of work, however, if
    needed, and should display fairly detailed logs of what it is doing.


Unfinished
~~~~~~~~~~

The above gives a functional site, but it is empty, and for testing some things
it would be better to have more data (e.g. users, groups, awards, verse sets).
Also, there are some CMS pages and chunks of content which exist only in the DB,
resulting in missing pages and bits of text when browsing the development site.

We need to fix this in a way that doesn't require downloading real user data to
the developers' machines.
