# -*- coding: utf8 -*-

from __future__ import unicode_literals

from collections import Counter
import glob
import hashlib
import pickle
import random
import re
import sys

import pykov

from bibleverses.models import get_whole_book, TextType, BIBLE_BOOKS, WordSuggestionData, split_into_words, is_punctuation, Verse, QAPair

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


TORAH = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']

HISTORY = ['Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Esther']

WISDOM = ['Job', 'Psalm', 'Proverbs', 'Ecclesiastes', 'Song of Solomon']

PROPHETS = ['Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi']

NT_HISTORY = ["Matthew", "Mark", "Luke", "John", "Acts"]

EPISTLES = ['Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation']

groups = [TORAH, HISTORY, WISDOM, PROPHETS, NT_HISTORY, EPISTLES]

MARKOV_CHAINS = {}


def similar_books(book_name):
    retval = []
    for g in groups:
        if book_name in g:
            retval.extend(g)
    if book_name not in retval:
        retval.append(book_name)
    return retval

def frequency_pairs(words):
    return scale_suggestions(Counter(words).items())


def generate_suggestions(version, ref=None, missing_only=True, thesaurus=None):
    def is_done(items):
        if missing_only:
            references = [item.reference for item in items]
            if version.word_suggestion_data.filter(reference__in=references).count() == len(references):
                # All done
                print "Skipping %s %s" % (version.slug, ' '.join(references))
                return True
        return False

    if version.text_type == TextType.BIBLE:
        for book in BIBLE_BOOKS:
            items = get_whole_book(book, version).verses
            if is_done(items):
                continue
            training_texts = {(version.slug, b): get_whole_book(b, version).text for b in similar_books(book)}
            print book
            generate_suggestions_helper(version, items,
                                        lambda verse: verse.text,
                                        training_texts, ref=ref, missing_only=missing_only,
                                        thesaurus=thesaurus)

    elif version.text_type == TextType.CATECHISM:
        items = list(version.qapairs.all())
        if is_done(items):
            return

        training_text = ' '.join(p.question + " " + p.answer for p in items)
        generate_suggestions_helper(version, items,
                                    lambda qapair: qapair.answer,
                                    {(version.slug, "all"): training_text},
                                    ref=ref, missing_only=missing_only,
                                    thesaurus=thesaurus)

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


def build_markov_chains_with_sentence_breaks(training_texts, size):
    return sum_matrices(build_markov_chains_for_text(key, training_text, size)
                        for key, training_text in training_texts.items())

def filename_for_labels(labels, size):
    return "../data/%s__level%s.markov.data" % ('_'.join(labels), str(size))


def load_saved_markov_data(label_set):
    keys = MARKOV_CHAINS.keys()
    loaded_labels = set([k[0] for k in keys])
    for labels in label_set:
        if labels not in loaded_labels:
            for fname in glob.glob(filename_for_labels(labels, '*')):
                print "loading %s" % fname
                MARKOV_CHAINS.update(pickle.load(file(fname)))


def hash_text(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


def build_markov_chains_for_text(labels, text, size):
    # Look in dict first
    labels = tuple(labels)
    if (labels, size) in MARKOV_CHAINS:
        return MARKOV_CHAINS[labels, size]

    sentences = text.split(".")
    v_accum, c_accum = pykov.maximum_likelihood_probabilities([])
    matrices = []
    print "Markov analysis level %d for %s" % (size, labels)
    for i, s in enumerate(sentences):
        if not s:
            continue
        words = split_into_words_for_suggestions(s)
        if size == 1:
            chain_input = words
        else:
            chain_input = [tuple(words[i:i+size]) for i in range(0, len(words)-(size-1))]
        v, c = pykov.maximum_likelihood_probabilities(chain_input, lag_time=1)
        matrices.append(c)

    retval = sum_matrices(matrices)
    new_data = {(labels, size): retval}
    MARKOV_CHAINS.update(new_data)
    fname = filename_for_labels(labels, size)
    with file(fname, "w") as f:
        sys.stdout.write("Writing %s..." % fname)
        pickle.dump(new_data, f)
    sys.stdout.write("done\n")
    return retval


def generate_suggestions_helper(version, items, text_getter, training_texts, ref=None,
                                missing_only=True, thesaurus=None):
    all_text = ' '.join(training_texts.values())
    first_words = sentence_first_words(all_text)
    first_word_frequencies = frequency_pairs(first_words)

    all_words = split_into_words_for_suggestions(all_text)
    markov_chains = {}

    def get_markov_chain(size):
        if size in markov_chains:
            return markov_chains[size]
        else:
            load_saved_markov_data(training_texts.keys())
            c = build_markov_chains_with_sentence_breaks(training_texts, size)
            markov_chains[size] = c
            return c

    def suggestions_thesaurus(words, i, count, suggestions_so_far):
        # Thesaurus strategy can be dumb, due to words that are e.g. both nouns
        # and verbs. Also, if suggestions are packed with synonyms, the basic
        # meaning will be obvious.  So, we limit the number. Also, we spread
        # them out 1.0 to 0.5 so there is a range.
        # Note that thesaurus returns words already ordered
        suggestions = thesaurus.get(words[i], [])[:MIN_SUGGESTIONS][:count]
        if len(suggestions) == 0:
            return []
        inc = 0.5 / len(suggestions)

        return [(w, 1.0 - (n * inc)) for n, w in enumerate(suggestions)]

    def suggestions_thesaurus_other(words, i, count, suggestions_so_far):
        count = max(count, 10)
        # This method tries to find some alternatives to words suggested by
        # non-thesaurus methods, to throw people off the scent!
        from_thesaurus = [w for w,f in suggestions_thesaurus(words, i, count, [])]
        retval = []
        new = set()
        for w, f in suggestions_so_far:
            if w not in from_thesaurus:
                more = thesaurus.get(w, [])[:2] # Just two for each
                for m in more:
                    if m not in new:
                        retval.append((m, f))
                        new.add(m)
            if len(retval) > count:
                return retval
        return retval

    def suggestions_first_word(words, i, count, suggestions_so_far):
        return first_word_frequencies[:]

    def mk_suggestions_markov(size):
        def suggestions_markov(words, i, count, suggestions_so_far):
            if size == 1:
                start = words[i-1]
            else:
                start = tuple(words[i-size:i])
            chain = get_markov_chain(size)
            options = chain.succ(start).items()
            return [(w if size == 1 else w[-1], f) for w, f in options]
        return suggestions_markov

    def suggestions_random_local(words, i, count, suggestions_so_far):
        count = max(count, 10)
        # Emphasise the words that come after the current one,
        # exclude the one immediately before as that is very unlikely,
        FACTOR = 5
        bag = words[i+1:] * FACTOR + words[:max(0, i-1)]
        if len(bag) == 0:
            return []
        c = Counter()
        # Try to cope with the fact that we'll get duplicates by boosting the
        # number we pick a bit.
        for i in range(0, int(count * FACTOR / 2)):
            c[random.choice(bag)] += 1
        return c.items()

    def suggestions_random_global(words, i, count, suggestions_so_far):
        count = max(count, 10)
        c = Counter()
        for i in range(0, count):
            c[random.choice(all_words)] += 1
        return c.items()

    MIN_SUGGESTIONS = 30
    MAX_SUGGESTIONS = 60

    # Strategies for finding alternatives, ordered according to how good they will be

    strategies = [
        (lambda i: i == 0, suggestions_first_word),
        (lambda i: i > 2, mk_suggestions_markov(3)),
        (lambda i: i > 1, mk_suggestions_markov(2)),
        # Thesaurus isn't always very good, because it can give the game away,
        # and also has some bizarre suggestions, so push down a bit
        (lambda i: thesaurus is not None, suggestions_thesaurus),
        # random from same verse are actually quite good,
        # because there are lots of cases where you can
        # miss out a word/phrase and it still makes sense
        (lambda i: True, suggestions_random_local),
        (lambda i: i > 0, mk_suggestions_markov(1)),
        (lambda i: True, suggestions_random_global),
        (lambda i: thesaurus is not None, suggestions_thesaurus_other),
    ]

    to_create = []
    for item in items:
        if ref is not None and item.reference != ref:
            continue

        text = text_getter(item)

        # Clear out old suggestions
        existing = version.word_suggestion_data.filter(reference=item.reference)
        if missing_only:
            if (existing.exists()):
                print "Skipping %s %s" % (version.slug, item.reference)
                continue
        else:
            existing.delete()
        print "%s %s" % (version.slug, item.reference)

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
                for condition, method in strategies:
                    if condition(i):
                        need = MIN_SUGGESTIONS - len(word_suggestions) # Only random strategies really uses this
                        new_suggestions = [(w,f) for (w,f) in method(words, i, need, word_suggestions)
                                           if w != word]
                        new_suggestions = scale_suggestions(new_suggestions, relevance)
                        if len(new_suggestions) > 0:
                            word_suggestions = merge_suggestions(word_suggestions, new_suggestions)
                            relevance = relevance / 2.0 # scale down worse methods for finding suggestions

                    # Sort after each one:
                    word_suggestions.sort(key=lambda (a,b): -b)

                word_suggestions = scale_suggestions(word_suggestions[0:MAX_SUGGESTIONS])

                # Add hits=0
                item_suggestions.append([(w,f,0) for w,f in word_suggestions])

        to_create.append(WordSuggestionData(version_slug=version.slug,
                                            reference=item.reference,
                                            suggestions=item_suggestions,
                                            hash=hash_text(text),
                                        ))

    WordSuggestionData.objects.bulk_create(to_create)


def scale_suggestions(suggestions, factor=1.0):
    # Scale frequencies to maximum of factor
    if len(suggestions) == 0:
        return suggestions
    max_f = max(f for w, f in suggestions)
    return [(w, float(f)/max_f * factor) for w, f in suggestions]

def merge_suggestions(s1, s2):
    return (Counter(dict(s1)) + Counter(dict(s2))).items()


def get_in_batches(qs, batch_size=200):
    start = 0
    while True:
        q = list(qs[start:start+batch_size])
        print start
        if len(q) == 0:
            raise StopIteration()
        for item in q:
            yield item
        start += batch_size


# Utility for checking our word suggestion generation:
def get_all_suggestion_words(version_name):
    s = set()
    for wd in get_in_batches(WordSuggestionData.objects.filter(version_slug=version_name)):
        for p in wd.get_suggestion_pairs():
            s |= set(w for w,f in p)
    return s


def get_all_version_words(version_name):
    text = []
    for verse in get_in_batches(Verse.objects.filter(version__slug=version_name)):
        text.extend(split_into_words_for_suggestions(verse.text))

    for qapair in get_in_batches(QAPair.objects.filter(catechism__slug=version_name)):
        text.extend(split_into_words_for_suggestions(qapair.answer))
    return Counter(text)
