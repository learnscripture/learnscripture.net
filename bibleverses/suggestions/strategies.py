import random
from collections import Counter

from .constants import (ALL_TEXT, FIRST_WORD_FREQUENCY_ANALYSIS, MIN_SUGGESTIONS, THESAURUS_ANALYSIS,
                        WORD_COUNTS_ANALYSIS, markov_analysis_for_size)
from .utils.numbers import weighted_choice


class SuggestionStrategy(object):
    """
    Suggestion strategy base class
    """
    # For convenience of use (in make_strategies) and to avoid repetitive init
    # methods, all strategies have the same constructor. If we want to set
    # other attributes, we use the `with_attributes` utility, which is enough
    # for needs at the current time.
    def __init__(self, training_texts):
        self.training_texts = training_texts

    @classmethod
    def with_attributes(cls, **kwargs):
        """
        Returns a constructor that additionally sets the passed in
        keyword arguments as attributes on the instance
        """
        def init(*args):
            instance = cls(*args)
            for k, v in kwargs.items():
                setattr(instance, k, v)
            return instance
        return init

    def load(self, storage):
        """
        Load any data needed from the storage, given the training_texts
        that apply for this instance.
        """
        # Usually this method will set up attributes on self for
        # later use.
        pass

    def use_for_word(self, word_idx):
        return True

    def get_suggestions(self, words, i, count, suggestions_so_far):
        raise NotImplementedError()


class ThesaurusSuggestions(SuggestionStrategy):

    def load(self, storage):
        # NB we always load thesaurus for complete text, ignoring
        # the keys in training_texts
        self.thesaurus = storage.load_analysis(THESAURUS_ANALYSIS,
                                               [(self.training_texts.text_slug, ALL_TEXT)])

    def get_suggestions(self, words, i, count, suggestions_so_far):
        # Thesaurus strategy can be dumb, due to words that are e.g. both nouns
        # and verbs. Also, if suggestions are packed with synonyms, the basic
        # meaning will be obvious.  So, we limit the number. Also, we spread
        # them out 1.0 to 0.5 so there is a range.
        # Note that thesaurus returns words already ordered
        suggestions = self.thesaurus.get(words[i], None)
        if suggestions is None:
            return []
        suggestions = suggestions[:MIN_SUGGESTIONS][:count]
        if len(suggestions) == 0:
            return suggestions
        inc = 0.5 / len(suggestions)

        return [(w, 1.0 - (n * inc)) for n, w in enumerate(suggestions)]


class ThesaurusSuggestionsOther(SuggestionStrategy):

    def load(self, storage):
        thesaurus_strategy = ThesaurusSuggestions(self.training_texts)
        thesaurus_strategy.load(storage)
        self.thesaurus_strategy = thesaurus_strategy
        self.thesaurus = thesaurus_strategy.thesaurus

    def get_suggestions(self, words, i, count, suggestions_so_far):
        # This method tries to find some alternatives to words suggested by
        # non-thesaurus methods, to throw people off the scent!
        count = min(count, 10)
        from_thesaurus = [w for w, f in self.thesaurus_strategy.get_suggestions(words, i, count, [])]
        retval = []
        new = set()
        for w, f in suggestions_so_far:
            if w not in from_thesaurus:
                more = self.thesaurus.get(w, [])[:2]  # Just two for each
                for m in more:
                    if m not in new:
                        retval.append((m, f))
                        new.add(m)
            if len(retval) > count:
                return retval
        return retval


class FirstWordSuggestions(SuggestionStrategy):

    def load(self, storage):
        self.first_word_frequencies = storage.load_analysis(FIRST_WORD_FREQUENCY_ANALYSIS,
                                                            self.training_texts.keys()).items()

    def use_for_word(self, word_idx):
        return word_idx == 0

    def get_suggestions(self, words, i, count, suggestions_so_far):
        return self.first_word_frequencies


class MarkovSuggestions(SuggestionStrategy):

    def load(self, storage):
        self.markov_chain = storage.load_analysis(markov_analysis_for_size(self.size),
                                                  self.training_texts.keys())

    def use_for_word(self, word_idx):
        return word_idx > self.size - 1

    def get_suggestions(self, words, i, count, suggestions_so_far):
        if self.size == 1:
            start = words[i - 1]
        else:
            start = tuple(words[i - self.size:i])
        return self.markov_chain.get_next_word_options(start)


class RandomLocalSuggestions(SuggestionStrategy):
    def get_suggestions(self, words, i, count, suggestions_so_far):
        count = min(count, 10)
        # Emphasise the words that come after the current one,
        # exclude the one immediately before as that is very unlikely,
        FACTOR = 5
        bag = words[i + 1:] * FACTOR + words[:max(0, i - 1)]
        if len(bag) == 0:
            return []
        c = Counter()
        # Try to cope with the fact that we'll get duplicates by boosting the
        # number we pick a bit.
        for i in range(0, int(count * FACTOR / 2)):
            c[random.choice(bag)] += 1
        return list(c.items())


class RandomGlobalSuggestions(SuggestionStrategy):

    def load(self, storage):
        self.global_word_counts = storage.load_analysis(WORD_COUNTS_ANALYSIS, self.training_texts.keys())

    def get_suggestions(self, words, i, count, suggestions_so_far):
        count = min(count, 10)
        c = Counter()
        global_word_counts_items = self.global_word_counts.items()
        for i in range(0, count):
            word = weighted_choice(global_word_counts_items)
            c[word] += 1
        return list(c.items())


STRATEGIES = [
    FirstWordSuggestions,
    MarkovSuggestions.with_attributes(size=3),
    MarkovSuggestions.with_attributes(size=2),
    # Thesaurus isn't always very good, because it can give the game away,
    # and also has some bizarre suggestions, so push down a bit
    ThesaurusSuggestions,
    # random from same verse are actually quite good,
    # because there are lots of cases where you can
    # miss out a word/phrase and it still makes sense
    RandomLocalSuggestions,
    MarkovSuggestions.with_attributes(size=1),
    RandomGlobalSuggestions,
    ThesaurusSuggestionsOther,
]


def make_strategies(training_texts):
    return [
        mk_strategy(training_texts)
        for mk_strategy in STRATEGIES
    ]
