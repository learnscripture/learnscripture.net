import sys


def intern_it(item):
    if isinstance(item, tuple | list):
        return item.__class__(intern_it(i) for i in item)
    elif isinstance(item, str):
        return sys.intern(item)
    else:
        return item
