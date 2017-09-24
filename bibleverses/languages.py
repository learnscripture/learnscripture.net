# -*- coding: utf8 -*-
import unicodedata

import attr

# We make Language a static class rather than DB, because
# supported languages always need code-level support.


@attr.s
class Language(object):
    # 2 leter ISO 639-1 code
    code = attr.ib()
    display_name = attr.ib()


LANGUAGE_CODE_EN = 'en'
LANGUAGE_CODE_TR = 'tr'

LANGUAGES = [
    Language(code=LANGUAGE_CODE_EN, display_name='English'),
    Language(code=LANGUAGE_CODE_TR, display_name='Türkçe'),
]

LANGUAGES_LOOKUP = {
    l.code: l for l in LANGUAGES
}

# Value for Django 'choices'
LANGUAGE_CHOICES = [
    (l.code, l.display_name) for l in LANGUAGES
]


def get_language(code):
    return LANGUAGES_LOOKUP[code]


DEFAULT_LANGUAGE = get_language('en')


def normalise_search_input_english(query):
    return query.strip().lower()


def normalise_search_input_turkish(query):
    query = query.strip().replace("'", "")
    # Turkish is often typed incorrectly with accents lost etc.
    # Strategy:
    #  - for codepoints that can be decomposed into accents,
    #    remove the accents.
    #  - replace ı with ı
    #  - throw everything else that is not ascii away.

    query = unicodedata.normalize('NFKD', query)
    query = query.replace('ı', 'i')
    query = query.encode('ascii', 'ignore').decode('ascii')
    query = query.lower()
    return query


_NORMALISE_SEARCH_FUNCS = {
    LANGUAGE_CODE_EN: normalise_search_input_english,
    LANGUAGE_CODE_TR: normalise_search_input_turkish
}


def normalise_search_input(language_code, query):
    return _NORMALISE_SEARCH_FUNCS[language_code](query.strip())
