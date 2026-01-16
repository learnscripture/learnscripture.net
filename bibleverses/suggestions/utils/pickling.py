import logging
import os.path
import pickle
from functools import wraps

from django.conf import settings

from .filesystem import ensure_dir

logger = logging.getLogger(__name__)

# This module exists in order to store intermediate results of analysis
# functions. The pickle format is not the final format that we save analysis
# results in.

# Some of these cached results can take a long time to rebuild, and require
# full access to the text to do so, so care should be taken before deleting
# the cached files, or changing this code in ways incompatible with the
# pickled data.


def cache_results_with_pickle(filename_suffix):
    """
    Decorator generator, takes a filename suffix to use for different functions.

    The actual function to be decorated should be a callable with a signature
    foo(training_texts, label, *args). Its results are cached using pickle and
    saving to disk.

    """

    # Note that the functions this is designed for take both 'training_texts'
    # and 'key'. This means they can avoid looking up the specific training text
    # if the result is already cached.
    def decorator(func):
        @wraps(func)
        def wrapper(training_texts, key, *args):
            # For sanity checking, both the pickled data and the filename
            # we save to include the key
            filename_key = "_".join(key)
            full_lookup_key = (key,) + tuple(args)

            if args:
                level = "__level" + "_".join(str(a) for a in args)
            else:
                level = ""
            fname = os.path.join(settings.DATA_ROOT, "wordsuggestions", f"{filename_key}{level}.{filename_suffix}.data")
            if os.path.exists(fname):
                logger.info("Loading %s", fname)
                new_data = pickle.load(open(fname, "rb"))
                return new_data[full_lookup_key]
            else:
                retval = func(training_texts, key, *args)

                new_data = {full_lookup_key: retval}
                ensure_dir(fname)
                with open(fname, "wb") as f:
                    logger.info("Writing %s...", fname)
                    pickle.dump(new_data, f)

                return retval

        return wrapper

    return decorator
