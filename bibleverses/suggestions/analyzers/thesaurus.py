import logging
import os.path
from typing import Callable

from django.conf import settings

from bibleverses.languages import LANG
from bibleverses.models import TextVersion
from bibleverses.suggestions.trainingtexts import TrainingTexts

from ..constants import ALL_TEXT, THESAURUS_ANALYSIS
from ..utils.models import get_all_version_words
from .base import Analyzer

logger = logging.getLogger(__name__)

Thesaurus = dict[str, list[str]]


def english_thesaurus() -> Thesaurus:
    fname = os.path.join(settings.SRC_ROOT, "resources", "thesaurus", "en.txt")
    f = open(fname, "rb").read().decode("utf8")
    thesaurus = {line.split(",")[0]: line.split(",")[1:] for line in f.split("\n")}

    # Thesaurus file tends to have unhelpful suggestions for pronouns, so we overwrite.
    # These are not synonyms, but likely alternatives
    OBJECTS = [
        "me",
        "you",
        "yourself",
        "oneself",
        "thee",
        "him",
        "her",
        "himself",
        "herself",
        "it",
        "itself",
        "us",
        "ourselves",
        "yourselves",
        "them",
        "themselves",
    ]
    SUBJECTS = ["i", "you", "thou", "he", "she", "it", "we", "they"]

    PRONOUN_THESAURUS = dict(
        [(k, [v for v in OBJECTS if v != k]) for k in OBJECTS]
        + [(k, [v for v in SUBJECTS if v != k]) for k in SUBJECTS]
    )

    thesaurus.update(PRONOUN_THESAURUS)
    return thesaurus


THESAURUSES: dict[str, Callable[[], Thesaurus]] = {
    LANG.EN: english_thesaurus,
    LANG.ES: lambda: {},  # Don't have Spanish thesaurus yet, and not sure how much it would help
}


class ThesaurusAnalyzer(Analyzer):
    name = THESAURUS_ANALYSIS

    def run(self, training_texts, keys):
        # For thesaurus, we always want to use the whole text, and have
        # a shared filename for the output, so override the key
        keys = [(training_texts.text_slug, ALL_TEXT)]
        return super().run(training_texts, keys)

    def analyze(self, training_texts: TrainingTexts, keys):
        return make_thesaurus(training_texts.text_version, disallow_text_loading=training_texts.disallow_loading)


def make_thesaurus(version: TextVersion, disallow_text_loading=False):
    thesaurus = THESAURUSES[version.language_code]()

    d = {}
    logger.info("Building thesaurus for %s\n", version.slug)
    words = get_all_version_words(version, disallow_text_loading=disallow_text_loading)
    for word, c in words.items():
        alts = thesaurus.get(word, None)
        if alts is None:
            continue

        # Don't allow multi-word alternatives
        alts = [a for a in alts if " " not in a]
        # Don't allow alternatives that don't appear in the text
        alts = [a for a in alts if a in words]
        # Normalize and exclude self
        alts = [a.lower() for a in alts if a != word]
        # Sort according to frequency in text
        alts_with_freq = [(words[a], a) for a in alts]
        alts_with_freq.sort(reverse=True)
        if len(alts_with_freq) == 0:
            continue
        d[word] = [w for c, w in alts_with_freq]
    return d
