=======
 Texts
=======

So far, relatively few Bible texts and catechisms have been added due to
permission problems.

As a result, and due to the fact that they sometimes come from different sources
(e.g. ESV via its web API), the process for adding them is not fully automated.
Some old scripts that were used (and probably won't run now) are found in
``scripts/``. The texts themselves are deliberately not stored in the repo
because of copyright, and because they would be large.

A further constraint is that the need to generate 'suggestions' for any text
(used in the 'on screen testing' method). This is done using Markov chain
analysis of the text, among other things, and requires the whole text to be
available first.


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

* Copy text data to live server.

  For catechisms:

  * Copy JSON file to live server::

      rsync ../texts/NCC.json learnscripture@learnscripture.net:/home/learnscripture

  * Load JSON file into live site::

      ssh learnscripture@learnscripture.net
      cd ~/webapps/learnscripture/verions/current/src
      . ../venv/bin/activate
      ./manage.py load_catechism NCC ~/NCC.json

   For Bibles, dump the relevant records from the ``bibleverses_verse`` table
   on the development machine, then transfer and load on the server. (Somehow -
   e.g. using the psql ``\copy`` command to dump to/from CSV).

* Dump the word suggestions and transfer to the server, OR, generate them on the
  server.

  Generate on the server::

    fab manage_py_command:"setup_bibleverse_suggestions <slug>"

  (This could take a while)

  Or, dump and transfer, e.g.::

      psql -U learnscripture -d learnscripture_wordsuggestions -c "\\copy (select version_slug, reference, hash, suggestions from bibleverses_wordsuggestiondata where version_slug = 'NCC') TO stdout WITH CSV HEADER;" > wsd_NCC.csv

      rsync wsd_NCC.csv learnscripture@learnscripture.net:/home/learnscripture

      psql -U learnscripture -d learnscripture_wordsuggestions -c "\\copy bibleverses_wordsuggestiondata (version_slug, reference, hash, suggestions) from stdin CSV HEADER" < ~/wsd_NCC.csv

   (This could take longer, depending on upload speeds...)

* Mark the text as public via the admin - then other people can start to use it.
