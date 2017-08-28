from collections import OrderedDict

from .utils import PicklerMixin
from ..utils.memory import intern_it


class Markov(PicklerMixin):
    # Interface for strategies:
    def get_next_word_options(self, start):
        try:
            options = list(self.pykov_succ_dict[start].items())
        except KeyError:
            return []
        return [(w if isinstance(w, str) else w[-1], f) for w, f in options]

    # Loading/saving
    format_version = 3

    def __init__(self, pykov_succ_dict):
        self.pykov_succ_dict = pykov_succ_dict

    @classmethod
    def from_pykov(cls, pykov_chain):
        # We could get further wins by rewriting the 'succ' method (from pykov)
        # using our own version, which is the only method we use after analysis is done,
        # so we can avoid loading pykov and numpy
        return cls(pykov_succ_dict(compress_pykov(pykov_chain)))


def pykov_succ_dict(pykov_chain):
    # This is copied from part of pykov.Matric.succ. All we need is the pykov
    # 'succ' method, and we don't want numpy dependencies
    _succ = OrderedDict([(state, OrderedDict()) for state in pykov_chain.states()])
    for link, probability in pykov_chain.items():
        _succ[link[0]][link[1]] = probability
    return _succ


def compress_pykov(pykov_chain):
    n = pykov_chain.__class__()
    for k, v in n.items():
        # key is a tuple of strings,
        # or a tuple of a tuple of strings
        n[intern_it(k)] = intern_it(v)
    return n
