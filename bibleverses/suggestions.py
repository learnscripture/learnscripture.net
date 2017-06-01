# -*- coding: utf8 -*-

from __future__ import unicode_literals

import gc
import hashlib
import logging
import os
import pickle
import random
import re
from collections import Counter

import pykov
from django.conf import settings

from bibleverses.models import (BIBLE_BOOKS, QAPair, TextType, TextVersion, Verse, WordSuggestionData, get_whole_book,
                                is_punctuation, split_into_words)
from bibleverses.services import partial_data_available
from learnscripture.utils.iterators import chunks

logger = logging.getLogger(__name__)


# -- Generate suggestions - top level code

# Normally generate_suggestions is called only by management command, for
# generating in bulk. However, at other times it has been necessary to edit a
# text via the admin, and this triggers 'fix_item' being called to fix up the
# word suggestions.

def fix_item(version_slug, reference):
    version = TextVersion.objects.get(slug=version_slug)
    # Before recreating, check if the hash has changed. This is especially
    # important for versions where we only partially store locally and have to
    # fetch the data again (triggering a save and this function being called)
    suggestion_data = WordSuggestionData.objects.filter(version_slug=version_slug,
                                                        reference=reference)
    item = version.get_item_by_reference(reference)
    if getattr(item, 'missing', False):
        return  # Doesn't need fixing

    if suggestion_data:
        saved_hash = suggestion_data[0].hash
        current_hash = hash_text(item.suggestion_text)
        if saved_hash == current_hash:
            logger.info("Skipping creation of word suggestions for unchanged %s %s",
                        version_slug, reference)
            return

    if partial_data_available(version_slug):
        # We are going to have problems fixing the word suggestions, because the
        # current algo assumes access to the whole text. So just log a warning
        logger.warn("Need to create word suggestions for %s %s but can't",
                    version_slug, reference)
        return
    generate_suggestions(version, missing_only=False, ref=reference)


def generate_suggestions(version, ref=None, missing_only=True):

    if version.text_type == TextType.BIBLE:
        if ref is not None:
            v = version.get_verse_list(ref)[0]
            book = BIBLE_BOOKS[v.book_number]
            items = [v]
            training_texts = get_training_texts_for_book(version, book)
            logger.info("Generating for %s", ref)
            generate_suggestions_for_items(
                version, items,
                training_texts, ref=ref, missing_only=missing_only)
        else:
            for book in BIBLE_BOOKS:
                generate_suggestions_for_book(version, book, missing_only=missing_only)

    elif version.text_type == TextType.CATECHISM:
        items = list(version.qapairs.all())
        if items_all_done(version, items, ref=ref, missing_only=missing_only):
            return

        training_text = ' '.join(p.question + " " + p.answer for p in items)
        generate_suggestions_for_items(
            version, items,
            {(version.slug, "all"): training_text},
            ref=ref, missing_only=missing_only)


def items_all_done(version, items, ref=None, missing_only=True):
    if missing_only:
        references = [item.reference for item in items]
        if ref is not None and ref not in references:
            return True
        if version.word_suggestion_data.filter(reference__in=references).count() == len(references):
            # All done
            logger.info("Skipping %s %s\n", version.slug, ' '.join(references))
            return True
    return False


def generate_suggestions_for_book(version, book, missing_only=True):
    logger.info("Generating for %s", book)
    items = get_whole_book(book, version).verses
    if items_all_done(version, items, missing_only=missing_only):
        return
    training_texts = get_training_texts_for_book(version, book)
    thesaurus = version_thesaurus(version)
    generate_suggestions_for_items(
        version, items,
        training_texts, missing_only=missing_only,
        thesaurus=thesaurus)


def get_training_texts_for_book(version, book):
    return {(version.slug, b): get_whole_book(b, version).text for b in similar_books(book)}


MIN_SUGGESTIONS = 20
MAX_SUGGESTIONS = 40


def generate_suggestions_for_items(version, items, training_texts, ref=None,
                                   missing_only=True, thesaurus=None):
    markov_chains_for_size = {}


    # Strategies for finding alternatives, ordered according to how good they will be

    strategies = [
        (lambda i: i == 0, FirstWordSuggestions(training_texts)),
        (lambda i: i > 2, MarkovSuggestions(3, markov_chains_for_size, training_texts)),
        (lambda i: i > 1, MarkovSuggestions(2, markov_chains_for_size, training_texts)),
        # Thesaurus isn't always very good, because it can give the game away,
        # and also has some bizarre suggestions, so push down a bit
        (lambda i: thesaurus is not None, ThesaurusSuggestions(thesaurus)),
        # random from same verse are actually quite good,
        # because there are lots of cases where you can
        # miss out a word/phrase and it still makes sense
        (lambda i: True, RandomLocalSuggestions()),
        (lambda i: i > 0, MarkovSuggestions(1, markov_chains_for_size, training_texts)),
        (lambda i: True, RandomGlobalSuggestions(training_texts)),
        (lambda i: thesaurus is not None, ThesaurusSuggestionsOther(thesaurus)),
    ]

    for batch in chunks(items, 100):
        batch = list(batch)  # need to iterate twice

        to_create = []
        to_delete = []
        if missing_only:
            existing_refs = set(
                version.word_suggestion_data
                .filter(reference__in=[i.reference for i in batch])
                .values_list('reference', flat=True))
        else:
            existing_refs = None

        for item in batch:
            generate_suggestions_single_item(version, item,
                                             strategies,
                                             ref=ref, missing_only=missing_only,
                                             existing_refs=existing_refs,
                                             to_create=to_create,
                                             to_delete=to_delete)
        if to_delete:
            logger.info("Deleting %s old items", len(to_delete))
            version.word_suggestion_data.filter(reference__in=to_delete).delete()
        if to_create:
            logger.info("Creating %s items", len(to_create))
            WordSuggestionData.objects.bulk_create(to_create)
        gc.collect()


def generate_suggestions_single_item(version, item,
                                     strategies,
                                     ref=None,
                                     missing_only=True,
                                     existing_refs=None,
                                     to_create=None,
                                     to_delete=None):
    if ref is not None and item.reference != ref:
        return

    text = item.suggestion_text

    if missing_only:
        if item.reference in existing_refs:
            # Don't recreate
            logger.info("Skipping %s %s", version.slug, item.reference)
            return
    else:
        # Clear out old suggestions first
        to_delete.append(item.reference)
    logger.info("Generating suggestions for %s %s", version.slug, item.reference)

    item_suggestions = []

    # We are actually treating beginning of verse as beginning of sentence,
    # which is not ideal, but hard to fix, and usually it's not too bad,
    # because verse breaks are usually 'close' to being sentence breaks.

    sentences = split_into_sentences(text)
    for sentence in sentences:
        words = split_into_words_for_suggestions(sentence)
        for i, word in enumerate(words):
            relevance = 1.0
            word_suggestions = []
            for condition, strategy in strategies:
                if condition(i):
                    need = MIN_SUGGESTIONS - len(word_suggestions)  # Only random strategies really uses this
                    new_suggestions = [(w, f) for (w, f) in
                                       strategy.get_suggestions(words, i, need, word_suggestions)
                                       if w != word]
                    new_suggestions = scale_suggestions(new_suggestions, relevance)
                    if len(new_suggestions) > 0:
                        word_suggestions = merge_suggestions(word_suggestions, new_suggestions)
                        relevance = relevance / 2.0  # scale down worse methods for finding suggestions

                # Sort after each one:
                word_suggestions.sort(key=lambda (w, f): -f)

            item_suggestions.append([w for w, f in word_suggestions[0:MAX_SUGGESTIONS]])

    to_create.append(WordSuggestionData(version_slug=version.slug,
                                        reference=item.reference,
                                        suggestions=item_suggestions,
                                        hash=hash_text(text),
                                        ))


class SuggestionStrategy(object):
    def get_suggestions(self, words, i, count, suggestions_so_far):
        raise NotImplementedError()


class ThesaurusSuggestions(SuggestionStrategy):
    def __init__(self, thesaurus):
        self.thesaurus = thesaurus

    def get_suggestions(self, words, i, count, suggestions_so_far):
        # Thesaurus strategy can be dumb, due to words that are e.g. both nouns
        # and verbs. Also, if suggestions are packed with synonyms, the basic
        # meaning will be obvious.  So, we limit the number. Also, we spread
        # them out 1.0 to 0.5 so there is a range.
        # Note that thesaurus returns words already ordered
        suggestions = self.thesaurus.get(words[i], [])[:MIN_SUGGESTIONS][:count]
        if len(suggestions) == 0:
            return []
        inc = 0.5 / len(suggestions)

        return [(w, 1.0 - (n * inc)) for n, w in enumerate(suggestions)]


class ThesaurusSuggestionsOther(SuggestionStrategy):
    def __init__(self, thesaurus):
        self.thesaurus = thesaurus
        self.thesaurus_strategy = ThesaurusSuggestions(thesaurus)

    def get_suggestions(self, words, i, count, suggestions_so_far):
        count = max(count, 10)
        # This method tries to find some alternatives to words suggested by
        # non-thesaurus methods, to throw people off the scent!
        from_thesaurus = [w for w, f in self.thesaurus_strategy.get_suggestions(words, i, count, [])]
        retval = []
        new = set()
        for w, f in suggestions_so_far:
            if w not in from_thesaurus:
                more = self.thesaurus.get(w, [])[:2]  # Just two for each
                for m in more:
                    if m not in new:
                        retval.append((m, f))
                        new.add(m)
            if len(retval) > count:
                return retval
        return retval


class FirstWordSuggestions(SuggestionStrategy):
    def __init__(self, training_texts):
        all_text = ' '.join(training_texts.values())
        first_words = sentence_first_words(all_text)
        self.first_word_frequencies = frequency_pairs(first_words)

    def get_suggestions(self, words, i, count, suggestions_so_far):
        return self.first_word_frequencies[:]


class MarkovSuggestions(SuggestionStrategy):
    def __init__(self, size, chain_storage, training_texts):
        self.size = size
        self.chain_storage = chain_storage
        self.training_texts = training_texts

    def get_suggestions(self, words, i, count, suggestions_so_far):
        if self.size == 1:
            start = words[i - 1]
        else:
            start = tuple(words[i - self.size:i])
        chain = self.get_markov_chain(self.size)
        try:
            options = chain.succ(start).items()
        except KeyError:
            return []
        return [(w if self.size == 1 else w[-1], f) for w, f in options]

    def get_markov_chain(self, size):
        # Due to being both memory and CPU intensive, and having limited memory
        # on the server, we cache carefully - not too much in memory or we run
        # out.
        if size in self.chain_storage:
            return self.chain_storage[size]
        else:
            c = build_markov_chains_with_sentence_breaks(self.training_texts, size)
            self.chain_storage[size] = c
            return c


class RandomLocalSuggestions(SuggestionStrategy):
    def get_suggestions(self, words, i, count, suggestions_so_far):
        count = max(count, 10)
        # Emphasise the words that come after the current one,
        # exclude the one immediately before as that is very unlikely,
        FACTOR = 5
        bag = words[i + 1:] * FACTOR + words[:max(0, i - 1)]
        if len(bag) == 0:
            return []
        c = Counter()
        # Try to cope with the fact that we'll get duplicates by boosting the
        # number we pick a bit.
        for i in range(0, int(count * FACTOR / 2)):
            c[random.choice(bag)] += 1
        return c.items()


class RandomGlobalSuggestions(SuggestionStrategy):
    def __init__(self, training_texts):
        all_text = ' '.join(training_texts.values())
        all_words = split_into_words_for_suggestions(all_text)
        self.all_words = all_words

    def get_suggestions(self, words, i, count, suggestions_so_far):
        count = max(count, 10)
        c = Counter()
        for i in range(0, count):
            c[random.choice(self.all_words)] += 1
        return c.items()


def scale_suggestions(suggestions, factor=1.0):
    # Scale frequencies to maximum of factor
    if len(suggestions) == 0:
        return suggestions
    max_f = max(f for w, f in suggestions)
    return [(w, float(f) / max_f * factor) for w, f in suggestions]


def merge_suggestions(s1, s2):
    return (Counter(dict(s1)) + Counter(dict(s2))).items()


def frequency_pairs(words):
    return scale_suggestions(Counter(words).items())


# -- Markov handling


def build_markov_chains_with_sentence_breaks(training_texts, size):
    return sum_matrices(build_markov_chains_for_text(key, training_text, size)
                        for key, training_text in training_texts.items())


def build_markov_chains_for_text(labels, text, size):
    # Look on disk first
    lookup_key = (labels, size)
    fname = filename_for_labels(labels, size)
    if os.path.exists(fname):
        logger.info("Loading %s", fname)
        new_data = pickle.load(file(fname))
        return new_data[lookup_key]

    # Else do calcs
    sentences = text.split(".")
    v_accum, c_accum = pykov.maximum_likelihood_probabilities([])
    matrices = []
    logger.info("Markov analysis level %d for %s", size, labels)
    for i, s in enumerate(sentences):
        if not s:
            continue
        words = split_into_words_for_suggestions(s)
        if size == 1:
            chain_input = words
        else:
            chain_input = [tuple(words[i:i + size]) for i in range(0, len(words) - (size - 1))]
        v, c = pykov.maximum_likelihood_probabilities(chain_input, lag_time=1)
        matrices.append(c)

    retval = sum_matrices(matrices)
    # For sanity check, we include the key in the stored data as well
    new_data = {lookup_key: retval}
    ensure_dir(fname)
    with file(fname, "w") as f:
        logger.info("Writing %s...", fname)
        pickle.dump(new_data, f)
    return retval


def filename_for_labels(labels, size):
    return os.path.join(settings.DATA_ROOT, "wordsuggestions", "%s__level%s.markov.data" % ('_'.join(labels), str(size)))


def hash_text(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


# Utility for checking our word suggestion generation:
def get_all_suggestion_words(version_name):
    s = set()
    for wd in get_in_batches(WordSuggestionData.objects.filter(version_slug=version_name)):
        for suggestions in wd.get_suggestions():
            s |= set(suggestions)
    return s


def get_all_version_words(version_name):
    text = []
    for verse in get_in_batches(Verse.objects.filter(version__slug=version_name)):
        text.extend(split_into_words_for_suggestions(verse.text))

    for qapair in get_in_batches(QAPair.objects.filter(catechism__slug=version_name)):
        text.extend(split_into_words_for_suggestions(qapair.answer))
    return Counter(text)


# -- Thesaurus

# Thesaurus file tends to have unhelpful suggestions for pronouns, so we overwrite.
# These are not synonyms, but likely alternatives
OBJECTS = ['me', 'you', 'yourself', 'oneself', 'thee', 'him', 'her', 'himself', 'herself', 'it', 'itself', 'us', 'ourselves', 'yourselves', 'them', 'themselves']
SUBJECTS = ['i', 'you', 'thou', 'he', 'she', 'it', 'we', 'they']

PRONOUN_THESAURUS = dict(
    [(k, [v for v in OBJECTS if v != k]) for k in OBJECTS] +
    [(k, [v for v in SUBJECTS if v != k]) for k in SUBJECTS]
)


def english_thesaurus():
    fname = os.path.join(settings.SRC_ROOT, 'resources', 'mobythes.aur')
    f = file(fname).read().decode('utf8')
    return dict((l.split(',')[0], l.split(',')[1:]) for l in f.split('\r'))


def ensure_dir(filename):
    d = os.path.dirname(filename)
    if not os.path.exists(d):
        os.makedirs(d)


def version_thesaurus(version):
    # Create a thesaurus specific to a version - i.e. start with english
    # thesaurus and throw out every word that isn't in the version text,
    # and other fixes.
    base_thesaurus = english_thesaurus()
    fname = os.path.join(settings.DATA_ROOT, "wordsuggestions", version.slug + ".thesaurus")
    ensure_dir(fname)
    try:
        logger.info("Loading thesaurus %s for %s\n", fname, version.slug)
        return pickle.load(file(fname))
    except IOError:
        pass

    thesaurus = base_thesaurus.copy()
    thesaurus.update(PRONOUN_THESAURUS)

    from bibleverses.suggestions import get_all_version_words
    d = {}
    logger.info("Building thesaurus for %s\n", version.slug)
    words = get_all_version_words(version.slug)
    for word, c in words.items():
        alts = thesaurus.get(word, None)
        if alts is None:
            d[word] = []
            continue

        # Don't allow multi-word alternatives
        alts = [a for a in alts if ' ' not in a]
        # Don't allow alternatives that don't appear in the text
        alts = [a for a in alts if a in words]
        # Normalise and exclude self
        alts = [a.lower() for a in alts if a != word]
        # Sort according to frequency in text
        alts_with_freq = [(words[a], a) for a in alts]
        alts_with_freq.sort(reverse=True)
        d[word] = [w for c, w in alts_with_freq]

    with file(fname, "w") as f:
        pickle.dump(d, f)
    return d


# -- Word and sentence mangling

PUNCTUATION = "!?,.<>()[];:\"'-–"
PUNCTUATION_OR_WHITESPACE = PUNCTUATION + " \n\r\t"
IN_WORD_PUNCTUATION = "'-"

# regexp for words with punctuation in the middle.
# We ignore digits, because things like 100,000 are allowed.
BAD_WORD_PUNCTUATION_RE = re.compile('[A-Za-z](' + "|".join(re.escape(p) for p in PUNCTUATION if p not in IN_WORD_PUNCTUATION) + ")[A-Za-z]")


# This is used for checking text before doing stats and finding suggestions
# for each word. bad_punctuation occasionally will produce false positives e.g.  NET Mark 11:32:
#
#   But if we say, 'From people - '" (they feared the crowd, for they all considered John to be truly a prophet).
#
# but the default way of calling split_into_words will fix this.

def bad_punctuation(text):
    words = split_into_words(text, fix_punctuation_whitespace=False)

    # Certain punctuation must not appear in middle of words
    # Ignore punctuation at end
    words = [w.strip(PUNCTUATION_OR_WHITESPACE) for w in words]
    if any(BAD_WORD_PUNCTUATION_RE.search(w) for w in words):
        return True

    # Check for pure punctuation with whitespace around it:
    # - but allow the following:
    #   -
    #   --
    # and punctuation that starts/ends with that.
    for chunk in text.split():
        if is_punctuation(chunk):
            if not any(chunk.startswith(a) or chunk.endswith(a) for a in ["--", "-"]):
                return True

    return False


def normalise_word(word):
    word = word.strip(PUNCTUATION_OR_WHITESPACE)
    return word.lower()


def split_into_words_for_suggestions(text):
    return map(normalise_word, split_into_words(text))


def split_into_sentences(text):
    return [s for s in [s.strip(PUNCTUATION_OR_WHITESPACE) for s in text.split('.')]
            if s]


def sentence_first_words(text):
    return [split_into_words_for_suggestions(l)[0]
            for l in split_into_sentences(text)]


# -- Matrices

def sum_matrices(matrices):
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


# -- Iteration utilities

def get_in_batches(qs, batch_size=200):
    start = 0
    while True:
        q = list(qs[start:start + batch_size])
        if len(q) == 0:
            raise StopIteration()
        for item in q:
            yield item
        start += batch_size


# -- Bible handling

TORAH = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']

HISTORY = ['Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Esther']

WISDOM = ['Job', 'Psalm', 'Proverbs', 'Ecclesiastes', 'Song of Solomon']

PROPHETS = ['Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi']

NT_HISTORY = ["Matthew", "Mark", "Luke", "John", "Acts"]

EPISTLES = ['Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation']

groups = [TORAH, HISTORY, WISDOM, PROPHETS, NT_HISTORY, EPISTLES]


def similar_books(book_name):
    retval = []
    for g in groups:
        if book_name in g:
            retval.extend(g)
    if book_name not in retval:
        retval.append(book_name)
    return retval
