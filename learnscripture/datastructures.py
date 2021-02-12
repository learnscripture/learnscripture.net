
class LazyDict:
    def __init__(self, source):
        self.source = source

    def __getitem__(self, item):
        return self.source(item)


class lazy_dict_like:
    """
    Used as a decorator to turn a method of a single
    parameter into a property that returns a dict-like
    object.

    Useful in Django templates which don't allow function/method calls, used in
    combination with 'lookup' template filter.

    """
    def __init__(self, method):
        self.method = method

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return LazyDict(lambda item: self.method(obj, item))
