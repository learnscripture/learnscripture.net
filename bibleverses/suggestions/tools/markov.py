from .utils import PicklerMixin


class Markov(PicklerMixin):
    # Interface for strategies:
    def get_next_word_options(self, start):
        try:
            options = list(self.pykov_chain.succ(start).items())
        except KeyError:
            return []
        return [(w if isinstance(w, str) else w[-1], f) for w, f in options]

    # Loading/saving
    format_version = 1

    def __init__(self, pykov_chain):
        self.pykov_chain = pykov_chain

    @classmethod
    def from_pykov(cls, pykov_chain):
        return cls(pykov_chain)
