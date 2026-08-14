from ..constants import FIRST_WORD_FREQUENCY_ANALYSIS
from ..utils.numbers import aggregate_word_counts, scale_suggestions, word_counts
from ..utils.pickling import cache_results_with_pickle
from ..utils.text import sentence_first_words
from .base import Analyzer


class FirstWordFrequencyAnalyzer(Analyzer):
    name = FIRST_WORD_FREQUENCY_ANALYSIS

    def analyze(self, training_texts, keys):
        return build_summed_scaled_first_word_counts(training_texts, keys)


def build_summed_scaled_first_word_counts(training_texts, keys):
    counts = [build_first_word_counts(training_texts, key) for key in keys]
    return scale_suggestions(list(aggregate_word_counts(counts).items()))


@cache_results_with_pickle("firstwordcounts")
def build_first_word_counts(training_texts, key):
    text = training_texts[key]
    first_words = sentence_first_words(text)
    return word_counts(first_words)
