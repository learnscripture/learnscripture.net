from .utils import PicklerMixin


class FirstWordFrequencies(PicklerMixin):
    # Interface for strategies:
    def items(self):
        return self.data

    # Factories/serialization:
    format_version = 1

    def __init__(self, data):
        self.data = data

    @classmethod
    def from_list(cls, data):
        return cls(data)
