import sys

from .utils import PicklerMixin


class Thesaurus(PicklerMixin):
    """
    Thesaurus object used by strategies
    """

    # Dictionary like interface for strategies to use:
    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default):
        if key in self.data:
            return self.data[key]
        return default

    # Factories/serialization:
    format_version = 1

    def __init__(self, data):
        self.data = data

    @classmethod
    def from_dict(cls, data):
        # Use sys.intern to reduce size of dictionary and 'dedupe' strings.
        # The saving due to interning appears to survive pickling/unpickling,
        # although the interning itself may not.
        # Running compress again after loading increases overall process
        # memory usage, so we don't bother doing that.
        return cls(compress(data))


def compress(data):
    compressed = {}
    for k, vs in data.items():
        compressed[sys.intern(k)] = list(map(sys.intern, vs))
    return compressed
