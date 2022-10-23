Adding a language
-----------------

Adding a new language will usually involve first adding a Bible for that
language, then later translating the interface for that language.

For adding a Bible in a new language
------------------------------------

- Add the new language code in LANG and LANGUAGES in languages.py
- Add a ``normalise_reference_input_`` function for the new language
- Add the Bible book names and variants in _BIBLE_BOOKS_FOR_LANG and
  _BIBLE_BOOK_ALTERNATIVES_FOR_LANG
- Update POSTGRES_SEARCH_CONFIGURATIONS
- Update Scores._LANGUAGE_POINTS_PER_WORD
- Update normalizeWordForText in Learn.elm as necessary to cope with accents

- Check how Bible reference parsing works in the language, and update
``bible_reference_parser_for_lang`` as needed You will then need to import the
Bible text, which is a separate task - see `<texts.rst>`_


For translating the interface into a new language
-------------------------------------------------

This is an entirely separate feature.

Main things needed:

- get translations for FTL files and add to project. See also
  `<ftl_primer.rst>`_ for notes to send to translators
- update ``LANGUAGES`` in settings.py
- do translations of page content in the CMS: https://learnscripture.net/admin/cms/
