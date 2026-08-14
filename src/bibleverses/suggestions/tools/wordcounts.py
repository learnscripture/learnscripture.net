from ..utils.numbers import weighted_random_choice
from .utils import PicklerMixin


class WordCounts(PicklerMixin):
    # Interface for strategies:
    def items(self):
        return self._items

    def weighted_random_choice_numpy(self):
        import numpy.random

        return numpy.random.choice(self._words, p=self._frequencies)

    def weighted_random_choice_python(self):
        return weighted_random_choice(self._items, total=self._total)

    # python version seems to be faster, and also we can eliminate numpy dependency.
    weighted_random_choice = weighted_random_choice_python

    # Factories/serialization:
    format_version = 2

    def __init__(self, counter):
        items = list(counter.items())
        self._items = items
        total = sum(count for word, count in items)
        self._total = total
        words, counts = zip(*items)
        frequencies = [count / total for count in counts]
        self._words = words
        self._frequencies = frequencies

    @classmethod
    def from_counter(cls, counter):
        return cls(counter)
