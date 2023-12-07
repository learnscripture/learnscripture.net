import logging

import pykov

from bibleverses.suggestions.trainingtexts import TrainingTexts

from ..constants import markov_analysis_name_for_size
from ..utils.numbers import sum_matrices
from ..utils.pickling import cache_results_with_pickle
from ..utils.text import split_into_words_for_suggestions
from .base import Analyzer

logger = logging.getLogger(__name__)


class MarkovAnalyzerBase(Analyzer):
    def analyze(self, training_texts, keys):
        return build_summed_markov_chains_for_texts(training_texts, keys, self.size)


class Markov1Analyzer(MarkovAnalyzerBase):
    size = 1
    name = markov_analysis_name_for_size(size)


class Markov2Analyzer(MarkovAnalyzerBase):
    size = 2
    name = markov_analysis_name_for_size(size)


class Markov3Analyzer(MarkovAnalyzerBase):
    size = 3
    name = markov_analysis_name_for_size(size)


def build_summed_markov_chains_for_texts(training_texts, keys, size):
    return sum_matrices(build_markov_chains_for_text(training_texts, key, size) for key in keys)


@cache_results_with_pickle("markov")
def build_markov_chains_for_text(training_texts: TrainingTexts, key, size):
    text = training_texts[key]
    sentences = text.split(".")
    v_accum, c_accum = pykov.maximum_likelihood_probabilities([])
    matrices = []
    logger.info("Markov analysis level %d for %s", size, key)
    for i, s in enumerate(sentences):
        if not s:
            continue
        words = split_into_words_for_suggestions(s)
        if size == 1:
            chain_input = words
        else:
            chain_input = [tuple(words[i : i + size]) for i in range(0, len(words) - (size - 1))]
        v, c = pykov.maximum_likelihood_probabilities(chain_input, lag_time=1)
        matrices.append(c)

    return sum_matrices(matrices)
