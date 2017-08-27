import gc
import resource

import pympler.asizeof

from .constants import ALL_TEXT, THESAURUS_ANALYSIS, BIBLE_BOOK_GROUPS
from .trainingtexts import BibleTrainingTexts, CatechismTrainingTexts
from .strategies import make_strategies
from .generate import generate_suggestions_for_text

from . import serverlogging  # noqa: F401

_last_mem_usage = 0

suffixes = ['b', 'Kb', 'Mb', 'Gb', 'Tb', 'Pb']


def nice_mem_units(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


def print_mem_usage(comment):
    global _last_mem_usage
    new_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    print(comment)
    print("Memory: " + nice_mem_units(new_usage))
    diff = new_usage - _last_mem_usage
    print("Difference: " + nice_mem_units(diff))
    _last_mem_usage = new_usage


def print_object_usage(object_name, obj):
    print(object_name + ": " + nice_mem_units(pympler.asizeof.asizeof(obj)))


def test_thesaurus_memory():
    print_mem_usage("Start")
    from .storage import AnalysisStorage
    s = AnalysisStorage()
    print_mem_usage("After creating storage")
    thesaurus = s.load_analysis(THESAURUS_ANALYSIS, [('NET', ALL_TEXT)])
    gc.collect()
    print_mem_usage("After loading NET thesaurus")
    print_object_usage("Thesaurus", thesaurus)


def strategies_for_bible_text(storage, text_slug):
    """
    Returns a dictionary with keys (text_slug, book name)
    and values as a list of strategies
    """
    retval = {}
    for book_group in BIBLE_BOOK_GROUPS:
        strategies = make_strategies(BibleTrainingTexts(text_slug=text_slug, books=book_group))
        # This strategies list can be used for each Bible book:
        for book in book_group:
            retval[text_slug, book] = strategies
    return retval


def strategies_for_catechism_text(storage, text_slug):
    return {(text_slug, ALL_TEXT):
            make_strategies(CatechismTrainingTexts(text_slug=text_slug))}


def test_server_usage():
    print_mem_usage("Start")
    from .storage import AnalysisStorage
    storage = AnalysisStorage()
    print_mem_usage("After creating storage")

    bible_versions = ['NET']
    catechism_versions = ['WSC', 'BC1695']
    all_strategies = {}
    for slug in bible_versions:
        all_strategies.update(strategies_for_bible_text(storage, slug))
    for slug in catechism_versions:
        all_strategies.update(strategies_for_catechism_text(storage, slug))

    print_mem_usage("After creating strategies")

    for strategies in all_strategies.values():
        for s in strategies:
            s.load(storage)

    print_mem_usage("After loading strategies")
    TEXT = "For God so loved the world, he gave his only begotten Son"

    for strategies in all_strategies.values():
        generate_suggestions_for_text(TEXT, strategies)
    print_mem_usage("After using all strategies")
    print_object_usage("storage", storage)
