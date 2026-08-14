from functools import wraps
from hashlib import sha1

from django.core.cache import cache as _djcache


def cache_results_key(f, args, kwargs):
    return sha1((str(f.__module__) + str(f.__name__) + str(args) + str(kwargs)).encode("utf-8")).hexdigest()


def cache_results(seconds=900):
    """
    Cache the result of a function call for the specified number of seconds,
    using Django's caching mechanism.
    Assumes that the function never returns None (as the cache returns None to indicate a miss), and that the function's result only depends on its parameters.
    Note that the ordering of parameters is important. e.g. myFunction(x = 1, y = 2), myFunction(y = 2, x = 1), and myFunction(1,2) will each be cached separately.

    Usage:

    @cache(600)
    def myExpensiveMethod(parm1, parm2, parm3):
        ....
        return expensiveResult

    """

    def do_cache(f):
        def x(*args, **kwargs):
            key = cache_results_key(f, args, kwargs)
            result = _djcache.get(key)
            if result is None:
                result = f(*args, **kwargs)
                _djcache.set(key, result, seconds)
            return result

        x.__name__ = f.__name__
        x.__doc__ = f.__doc__
        x.__module__ = f.__module__
        return x

    return do_cache


def clear_cache_results(f, *args, **kwargs):
    key = cache_results_key(f, args, kwargs)
    _djcache.delete(key)


def memoize_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        if key in wrapper.__result_cache:
            return wrapper.__result_cache[key]
        retval = func(*args, **kwargs)
        wrapper.__result_cache[key] = retval
        return retval

    def clearer():
        wrapper.__result_cache = {}

    clearer()
    wrapper.clear_result_cache = clearer

    return wrapper
