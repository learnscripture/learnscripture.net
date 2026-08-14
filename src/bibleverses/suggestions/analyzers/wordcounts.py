from collections import Counter

from ..constants import WORD_COUNTS_ANALYSIS
from ..utils.numbers import aggregate_word_counts
from ..utils.pickling import cache_results_with_pickle
from ..utils.text import split_into_words_for_suggestions
from .base import Analyzer


class WordCountsAnalyzer(Analyzer):
    name = WORD_COUNTS_ANALYSIS

    def analyze(self, training_texts, keys):
        return get_text_word_counts(training_texts, keys)


def get_text_word_counts(training_texts, keys):
    return aggregate_word_counts(get_word_counts(training_texts, key) for key in keys)


@cache_results_with_pickle("wordcounts")
def get_word_counts(training_texts, key):
    text = training_texts[key]
    words = split_into_words_for_suggestions(text)
    return Counter(words)
