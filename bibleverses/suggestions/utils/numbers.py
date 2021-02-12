import operator
import random
from collections import Counter
from functools import reduce


def sum_matrices(matrices):
    import pykov

    # Do our own matrix sum to avoid n^2 behaviour
    retval = pykov.Matrix()
    keys = []
    matrices = list(matrices)
    for m in matrices:
        keys.extend(m.keys())
    keys = set(keys)
    for k in keys:
        retval[k] = sum(m[k] for m in matrices)
    return retval


# Counting:

def word_counts(words):
    return Counter(words)


def aggregate_word_counts(counts):
    return reduce(operator.add, counts)


def normalize_probabilities(f):
    sm = sum(f.values())
    retval = f.__class__()
    for k, v in f.items():
        retval[k] = (1.0 * v) / sm
    return retval


def merge_suggestions(s1, s2):
    return list((Counter(dict(s1)) + Counter(dict(s2))).items())


def scale_suggestions(suggestions, factor=1.0):
    if len(suggestions) == 0:
        return suggestions
    # Scale frequencies to maximum of factor
    max_f = max(f for w, f in suggestions)
    return [(w, float(f) / max_f * factor) for w, f in suggestions]


def weighted_random_choice(choices, total=1):
    """
    Returns a weighted random choice from a list of (choice, frequency)
    pairs. The frequencies in the list must add up to 1,
    or pass the total.
    """
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        upto += w
        if upto >= r:
            return c
    assert False, "Shouldn't get here"
