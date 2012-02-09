

class LazyDict(object):
    def __init__(self, func, args, kwargs, expected_keys):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.data = None
        self.expected_keys = set(expected_keys)

    def _evaluate(self):
        self.data = self.func(*self.args, **self.kwargs)

    def __getitem__(self, key):
        if key in self.expected_keys:
            if self.data is None:
                self._evaluate()
            return self.data[key]
        else:
            raise KeyError()

    def __contains__(self, key):
        if key not in self.expected_keys:
            return False
        if self.data is None:
            self._evaluate()
        return key in self.data


def lazy_dict(func, expected_keys):
    """
    Given a function that returns a dictionary containing at most the keys in
    expected_keys, returns a dictionary that will lazily evaluate the function
    to get the values of the keys, but only when a key in expected_keys is asked
    for.

    Useful for turning a context processor into a lazy context processor.

    (This works because of that fact that RequestContext/Context act as a stack
    of dictionaries, so we don't need to actually combine the contents of the
    dictionary with another dictionary).
    """
    def inner(*args, **kwargs):
        return LazyDict(func, args, kwargs, expected_keys)
    return inner
