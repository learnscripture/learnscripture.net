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
    EN = "en"
    TR = "tr"

    # Code for language agnostic name
    INTERNAL = "internal"


LANGUAGES = [
    Language(code=LANG.EN, display_name="English"),
    Language(code=LANG.TR, display_name="Türkçe"),
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


_NORMALIZE_SEARCH_FUNCS = {
    LANG.EN: normalize_reference_input_english,
    LANG.TR: normalize_reference_input_turkish,
    LANG.INTERNAL: lambda x: x,
}


def normalize_reference_input(language_code, query):
    return _NORMALIZE_SEARCH_FUNCS[language_code](query.strip())
