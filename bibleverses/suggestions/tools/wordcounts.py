from .utils import PicklerMixin


class WordCounts(PicklerMixin):
    # Interface for strategies:
    def items(self):
        return self.counter.items()

    # Factories/serialization:
    format_version = 1

    def __init__(self, counter):
        self.counter = counter

    @classmethod
    def from_counter(cls, counter):
        return cls(counter)
