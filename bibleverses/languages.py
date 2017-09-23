import attr

# We make Language a static class rather than DB, because
# supported languages always need code-level support.


@attr.s
class Language(object):
    # 2 leter ISO 639-1 code
    code = attr.ib()
    display_name = attr.ib()


LANGUAGE_CODE_EN = 'en'

LANGUAGES = [
    Language(code=LANGUAGE_CODE_EN, display_name='English'),
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
