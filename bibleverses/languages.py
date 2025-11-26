"""
Definition of languages supported for Bible texts.
"""
# See also bibleverses.constants for Bible book names

# For interface languages, see settings.py

import re
import unicodedata
from dataclasses import dataclass


@dataclass
class Language:
    """
    Metadata for a language
    """

    # We make Language a static class rather than DB, because
    # supported languages always need code-level support.

    code: str  # 2 leter ISO 639-1 code
    display_name: str


class LANG:
    """
    Holder for language codes
    """

    # These must correspond with the HTML lang attribute values. i.e. 2 letter, ISO
    # 639-1 codes in most cases.
    EN = "en"  # English
    TR = "tr"  # Turkish
    NL = "nl"  # Dutch
    ES = "es"  # Spanish
    ZH_HANT = "zh-Hant"  # Chinese (Traditional)
    ZH_HANS = "zh-Hans"  # Chinese (Simplified)

    # Code for language agnostic name
    INTERNAL = "internal"


LANGUAGES = [
    Language(code=LANG.EN, display_name="English"),
    Language(code=LANG.NL, display_name="Nederlands"),
    Language(code=LANG.TR, display_name="Türkçe"),
    Language(code=LANG.ES, display_name="Español"),
    Language(code=LANG.ZH_HANT, display_name="中文（繁體）"),
    Language(code=LANG.ZH_HANS, display_name="中文（简体）"),
]

LANGUAGES_LOOKUP = {lang.code: lang for lang in LANGUAGES}

# Value for Django 'choices'
LANGUAGE_CHOICES = [(lang.code, lang.display_name) for lang in LANGUAGES]


def get_language(code: str) -> Language:
    return LANGUAGES_LOOKUP[code]


DEFAULT_LANGUAGE: Language = get_language(LANG.EN)


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

    query = unicodedata.normalize("NFKD", query)
    query = query.replace("ı", "i")
    query = query.encode("ascii", "ignore").decode("ascii")
    query = query.lower()
    return query


def normalize_reference_input_dutch(query: str) -> str:
    query = query.strip().replace("'", "")
    # Strategy:
    #  - for codepoints that can be decomposed into accents,
    #    remove the accents.
    #  - throw everything else that is not ascii away.
    query = unicodedata.normalize("NFKD", query)
    query = query.encode("ascii", "ignore").decode("ascii")
    query = query.lower()
    return query


def normalize_reference_input_spanish(query: str) -> str:
    query = query.strip().replace("'", "")
    # Strategy:
    #  - for codepoints that can be decomposed into accents,
    #    remove the accents.
    #  - throw everything else that is not ascii away.
    query = unicodedata.normalize("NFKD", query)
    query = query.encode("ascii", "ignore").decode("ascii")
    query = query.lower()
    return query


def normalize_reference_input_chinese(query):
    # Chinese doesn't have case, so just strip whitespace
    query = query.strip()
    # Add a space between Chinese characters and digits to allow references like "詩篇2"
    # to work the same as "詩篇 2"
    # Insert space between Chinese character and digit if not already present
    query = re.sub(r'([\u4e00-\u9fff])(\d)', r'\1 \2', query)
    return query


_NORMALIZE_SEARCH_FUNCS = {
    LANG.EN: normalize_reference_input_english,
    LANG.TR: normalize_reference_input_turkish,
    LANG.NL: normalize_reference_input_dutch,
    LANG.ES: normalize_reference_input_spanish,
    LANG.ZH_HANT: normalize_reference_input_chinese,
    LANG.ZH_HANS: normalize_reference_input_chinese,
    LANG.INTERNAL: lambda x: x,
}


def normalize_reference_input(language_code: str, query: str) -> str:
    return _NORMALIZE_SEARCH_FUNCS[language_code](query.strip())
