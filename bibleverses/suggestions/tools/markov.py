from .utils import PicklerMixin
from ..utils.memory import intern_it


class Markov(PicklerMixin):
    # Interface for strategies:
    def get_next_word_options(self, start):
        try:
            options = list(self.pykov_chain.succ(start).items())
        except KeyError:
            return []
        return [(w if isinstance(w, str) else w[-1], f) for w, f in options]

    # Loading/saving
    format_version = 2

    def __init__(self, pykov_chain):
        self.pykov_chain = pykov_chain

    @classmethod
    def from_pykov(cls, pykov_chain):
        return cls(compress_pykov(pykov_chain))


def compress_pykov(pykov_chain):
    n = pykov_chain.__class__()
    for k, v in n.items():
        # key is a tuple of strings,
        # or a tuple of a tuple of strings
        n[intern_it(k)] = intern_it(v)
    return n
