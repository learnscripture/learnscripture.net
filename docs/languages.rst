Adding a language
-----------------

Adding a new language will usually involve first adding a Bible for that
language, then later translating the interface for that language.

For adding a Bible in a new language
------------------------------------

- Add the new language code in LANG and LANGUAGES in languages.py
- Add a ``normalize_reference_input_`` function for the new language
- Add the Bible book names and variants in _BIBLE_BOOKS_FOR_LANG and _BIBLE_BOOK_ALTERNATIVES_FOR_LANG
- Update POSTGRES_SEARCH_CONFIGURATIONS
- Update Scores._LANGUAGE_POINTS_PER_WORD
- Update ``normalizeWordForTest`` in Learn.elm as necessary to cope with accents, adding a ``simplifyXXX`` if needed
- Update ``stripOuterPunctuation`` in Learn.elm as necessary to cope with punctuation, expanding the tests if needed.
- Check how Bible reference parsing works in the language, and update ``bible_reference_parser_for_lang`` as needed
- You will then need to import the Bible text, which is a separate task - see `<texts.rst>`_
- If we want to enable “On screen buttons” aka word suggestions:
  - update THESAURUSES in bibleverses/suggestions/analyzers/thesaurus.py
  - check with a relevant expert that the word suggestion generator produces decent results


For translating the interface into a new language
-------------------------------------------------

This is an entirely separate feature.

Main things needed:

- get translations for FTL files and add to project. See also
  `<ftl_primer.rst>`_ for notes to send to translators
- update ``LANGUAGES`` in settings.py
- do translations of page content in the CMS: https://learnscripture.net/admin/cms/
- update l10n.toml


Checks
------

Various checks are run as part of deployment, and can be run manually::

  fab check-ftl
