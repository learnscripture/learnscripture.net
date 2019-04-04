=======
 Texts
=======

So far, relatively few Bible texts and catechisms have been added due to
permission problems.

As a result, and due to the fact that they sometimes come from different sources
(e.g. ESV via its web API), the process for adding them is not fully automated.
Some old scripts that were used (and probably won't run now) are found in
``scripts/``. The texts themselves are deliberately not stored in the repo
because of copyright, and because they would be large. Some of the texts are
available in the learnscripture-texts repo, where there are not copyright
issues.

A further constraint is the need to generate 'suggestions' for any text
(used in the 'on screen testing' method). This is done using Markov chain
analysis of the text, among other things, and requires the whole text to be
available first.

The Markov chain analysis and other methods are almost certainly only appropriate
for English language texts - in fact these methods use an English thesaurus and a few
sets of hard-coded English tables (e.g. for pronouns) as part of this process.
This presents a challenge if other languages are wanted. In particular, the methods
are likely to work badly for languages with a lot of grammatical inflections
on words (which English does not have). For these languages, generating word
plausible word suggestions for the on-screen testing method would be a bigger
challenge.


New texts and catechisms
========================

* First, ascertain copyright and usage constraints, obviously. The
  ``TextVersion.url`` field can be used for linking back to a website, but note
  that this is only displayed on some page. It may be helpful to cover
  ourselves by adding a link in the footer.

* The text needs to be prepared and loaded into the database in the development
  environment. This involves creating a TextVersion record in the admin, and then adding:

  * For Bibles, Verse instances corresponding to every Verse in the KJV
    (including missing verses, which should be marked with missing=True).

    The exact process for doing this is not automated. In many cases you will need
    to write a script. The most recent ``import_XXX.py`` script located in the
    ``scripts`` folder in the ``texts`` repository may be a good start.

    Set LOADING_VERSES = True in settings to stop suggestions being created while you are
    doing this.

  * For catechisms, QAPairs for each question.

    Create JSON file with a list of [number, question, answer]

    run: ``./manage.py load_catechism <slug> <json_filename>``

* First ``./manage.py run_suggestions_analyzers`` then
  ``./manage.py setup_bibleverse_suggestions`` needs to be run, passing the version
  slug as an argument in both cases.

* Test locally, ensure it works as expected.

* Copy text data to live server.

  * First, make the text non-public in the local development database using the
    Django admin, so that it will be initially non-public when uploaded.

  * Then, dump from development e.g.::

      $ ./manage.py dump_text ../texts/db_dumps <slug>

  * Transfer to live server e.g.::

      $ rsync ../texts/db_dumps/<slug>.* learnscripture@learnscripture.net:/home/learnscripture/texts

  * Load JSON file into live site::

      $ ssh learnscripture@learnscripture.net
      $ cd ~/webapps/learnscripture/versions/current/src
      $ . ../venv/bin/activate
      $ ./manage.py load_text ~/texts <slug>

* Dump the word suggestions and transfer to the server, OR, generate them on the
  server.

  Generate on the server::

    fab manage_py_command:"run_suggestions_analyzers <slug>"
    fab manage_py_command:"setup_bibleverse_suggestions <slug>"

  (This could take a while. Also, note that there are issues with texts
  that are only partially available in the local database e.g. ESV.)

  Or, dump and transfer, e.g.::

      psql -U learnscripture -d learnscripture_wordsuggestions -c "\\copy (select version_slug, localized_reference, hash, suggestions from bibleverses_wordsuggestiondata where version_slug = '<slug>') TO stdout WITH CSV HEADER;" > wsd_<slug>.csv

      rsync wsd_<slug>.csv learnscripture@learnscripture.net:/home/learnscripture

      psql -U learnscripture -d learnscripture_wordsuggestions -c "\\copy bibleverses_wordsuggestiondata (version_slug, localized_reference, hash, suggestions) from stdin CSV HEADER" < ~/wsd_<slug>.csv

   (This could take longer, depending on upload speeds...)

* Mark the text as public via the admin - then other people can start to use it.
