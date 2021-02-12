# -*- coding: utf-8 -*-
import unicodedata

import attr

# We make Language a static class rather than DB, because
# supported languages always need code-level support.


@attr.s
class Language(object):
    # 2 leter ISO 639-1 code
    code = attr.ib()
    display_name = attr.ib()


# These must correspond with the HTML lang attribute values. i.e. 2 letter, ISO
# 639-1 codes in most cases.
LANGUAGE_CODE_EN = 'en'
LANGUAGE_CODE_TR = 'tr'

# Code for language agnostic name
LANGUAGE_CODE_INTERNAL = 'internal'

LANGUAGES = [
    Language(code=LANGUAGE_CODE_EN, display_name='English'),
    Language(code=LANGUAGE_CODE_TR, display_name='Türkçe'),
]

LANGUAGES_LOOKUP = {
    lang.code: lang for lang in LANGUAGES
}

# Value for Django 'choices'
LANGUAGE_CHOICES = [
    (lang.code, lang.display_name) for lang in LANGUAGES
]


def get_language(code):
    return LANGUAGES_LOOKUP[code]


DEFAULT_LANGUAGE = get_language('en')


def normalize_reference_input_english(query):
    return query.strip().lower()


def normalize_reference_input_turkish(query):
    query = query.strip().replace("'", "")
    # Turkish is often typed incorrectly with accents lost etc.
    # Strategy:
    #  - for codepoints that can be decomposed into accents,
    #    remove the accents.
    #  - replace ı with i
    #  - throw everything else that is not ascii away.

    query = unicodedata.normalize('NFKD', query)
    query = query.replace('ı', 'i')
    query = query.encode('ascii', 'ignore').decode('ascii')
    query = query.lower()
    return query


_NORMALIZE_SEARCH_FUNCS = {
    LANGUAGE_CODE_EN: normalize_reference_input_english,
    LANGUAGE_CODE_TR: normalize_reference_input_turkish,
    LANGUAGE_CODE_INTERNAL: lambda x: x,
}


def normalize_reference_input(language_code, query):
    return _NORMALIZE_SEARCH_FUNCS[language_code](query.strip())
