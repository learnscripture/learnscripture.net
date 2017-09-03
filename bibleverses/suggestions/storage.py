"""
Handles stored analysis
"""
import hashlib
import logging
import os.path

import attr

from .constants import (FIRST_WORD_FREQUENCY_ANALYSIS, MARKOV_1_ANALYSIS, MARKOV_2_ANALYSIS, MARKOV_3_ANALYSIS,
                        THESAURUS_ANALYSIS, WORD_COUNTS_ANALYSIS)
from .exceptions import AnalysisMissing
from .tools.firstwordfrequencies import FirstWordFrequencies
from .tools.markov import Markov
from .tools.thesaurus import Thesaurus
from .tools.wordcounts import WordCounts

# We don't use django settings to avoid a runtime dependency on Django. We also
# are careful to not import analyzers, because they can import the rest of the
# project, and we want this module to be used without doing that. That constrains
# some of the design decisions about how to link up Analyzers and Stragies.

# Also, some Stratgies use the same analysis, so we need to avoid loading twice.

logger = logging.getLogger(__name__)

rel = lambda *x: os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), *x))
DATA_ROOT = rel("..", "..", "..", "data")


@attr.s
class Serializer(object):
    """
    Definition of something used to convert output of analysis (from Analyzer class)
    to something that can be used by strategies and is serializable (in a memory efficient way).
    """
    # Unique name, usually that of Analyzer class
    name = attr.ib()
    # Callable that converts data as returned by an Analyzer to a format for
    # serializing, deserializing and using by a strategy.
    from_analyzer = attr.ib()
    # Callable that takes an object and file handle and serializes data to it.
    dump = attr.ib()
    # Callable that takes a file handle and deserializes data
    load = attr.ib()
    # A format version. This can be bumped if the format changes, so that
    # a new analysis file is created.
    format_version = attr.ib()


SERIALIZERS = [
    Serializer(WORD_COUNTS_ANALYSIS, WordCounts.from_counter,
               WordCounts.dump, WordCounts.load, WordCounts.format_version),
    Serializer(THESAURUS_ANALYSIS, Thesaurus.from_dict,
               WordCounts.dump, Thesaurus.load, Thesaurus.format_version),
    Serializer(FIRST_WORD_FREQUENCY_ANALYSIS, FirstWordFrequencies.from_list,
               FirstWordFrequencies.dump, FirstWordFrequencies.load, FirstWordFrequencies.format_version),
    Serializer(MARKOV_1_ANALYSIS, Markov.from_pykov,
               Markov.dump, Markov.load, Markov.format_version),
    Serializer(MARKOV_2_ANALYSIS, Markov.from_pykov,
               Markov.dump, Markov.load, Markov.format_version),
    Serializer(MARKOV_3_ANALYSIS, Markov.from_pykov,
               Markov.dump, Markov.load, Markov.format_version),
]

SERIALIZER_DICT = {s.name: s for s in SERIALIZERS}


class AnalysisStorage(object):
    def __init__(self):
        self.loaded = {}

    def saved_analysis_exists(self, analyzer, training_text_keys):
        filename = self._storage_name_for_analysis(analyzer=analyzer,
                                                   training_text_keys=training_text_keys)
        return os.path.exists(filename)

    def save_analysis(self, data, analyzer, training_text_keys):
        serializer = self._serializer_for_analyzer(analyzer)
        filename = self._storage_name_for_analysis(analyzer=analyzer,
                                                   training_text_keys=training_text_keys)
        transformed_data = serializer.from_analyzer(data)
        logger.info("Saving analysis %s for keys %s\n", serializer.name, training_text_keys)
        with open(filename, "wb") as f:
            logger.info("..into file %s\n", filename)
            serializer.dump(transformed_data, f)

    def _serializer_for_analyzer(self, analyzer):
        name = analyzer.name
        if name is NotImplemented:
            raise NotImplementedError("Need to add 'name' to {0}".format(analyzer))
        return self._serializer_for_analyzer_name(name)

    def _serializer_for_analyzer_name(self, name):
        return SERIALIZER_DICT[name]

    def load_analysis(self, analyzer_name, training_text_keys):
        training_text_keys = list(training_text_keys)
        filename = self._storage_name_for_analysis(analyzer_name=analyzer_name,
                                                   training_text_keys=training_text_keys)
        if filename in self.loaded:
            return self.loaded[filename]
        serializer = self._serializer_for_analyzer_name(analyzer_name)
        logger.info("Loading analysis %s for keys %s\n", serializer.name, training_text_keys)
        if not os.path.exists(filename):
            raise AnalysisMissing("Analysis file %s missing for analysis %s, text %r" %
                                  (filename, serializer.name, training_text_keys))
        with open(filename, "rb") as f:
            logger.info("...from file %s\n", filename)
            retval = serializer.load(f)
            self.loaded[filename] = retval
            return retval

    def _name_and_format_for_analyzer(self, analyzer):
        return analyzer.name, self._serializer_for_analyzer(analyzer).format_version

    def _storage_name_for_analysis(self,
                                   analyzer=None,
                                   analyzer_name=None,
                                   training_text_keys=None):
        if analyzer is not None:
            serializer = self._serializer_for_analyzer(analyzer)
        else:
            serializer = self._serializer_for_analyzer_name(analyzer_name)
        filename_key = ','.join('_'.join(k) for k in training_text_keys)

        # "File name too long" problem - we reduce size by taking a hash.
        # In all cases, the first part of each training key is the same (the text slug),
        # so we increase readability by keeping that bit plain.
        key_first_parts = set(k1 for k1, k2 in training_text_keys)  # Always length 1
        filename_first_part = '_'.join(key_first_parts)
        filename_key = "SHA1_" + hashlib.sha1(filename_key.encode('utf-8')).hexdigest()[0:8]

        filename = ".".join(
            [serializer.name,
             filename_first_part,
             filename_key,
             str(serializer.format_version),
             'analysisdata',
             ])
        return os.path.join(
            DATA_ROOT,
            "wordsuggestions",
            filename)
