"""
Utilities that deal with LearnScripture models, particularly bibleverses.models
"""
from bibleverses.books import get_bible_books
from bibleverses.models import TextType, WordSuggestionData

from .iterators import get_in_batches

# This module can have a dependency on Django


def get_all_version_words(version, disallow_text_loading=False):
    from ..analyzers.wordcounts import get_text_word_counts
    from ..trainingtexts import BibleTrainingTexts, CatechismTrainingTexts

    if version.text_type == TextType.BIBLE:
        training_texts = BibleTrainingTexts(
            text_version=version,
            books=get_bible_books(version.language_code),
            disallow_loading=disallow_text_loading,
        )
    elif version.text_type == TextType.CATECHISM:
        training_texts = CatechismTrainingTexts(text_version=version, disallow_loading=disallow_text_loading)

    return get_text_word_counts(training_texts, list(training_texts.keys()))


def get_all_suggestion_words(version_name):
    s = set()
    for wd in get_in_batches(WordSuggestionData.objects.filter(version_slug=version_name)):
        for suggestions in wd.get_suggestions():
            s |= set(suggestions)
    return s
