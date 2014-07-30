from collections import Counter
import hashlib
import random
import re

import pykov

from bibleverses.models import get_whole_book, TextType, BIBLE_BOOKS, WordSuggestionData, split_into_words, is_punctuation, Verse, QAPair

PUNCTUATION = "!?,.<>()[];:\"'-"
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
    words = [w.strip(PUNCTUATION) for w in words]
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
    word = word.strip(PUNCTUATION)
    return word.lower().strip()


def split_into_words_for_suggestions(text):
    return map(normalise_word, split_into_words(text))


def sentence_first_words(text):
    return [split_into_words_for_suggestions(l)[0]
            for l in text.split('.')
            if l]


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
            training_text = " ".join(get_whole_book(b, version).text for b in similar_books(book))
            print book
            generate_suggestions_helper(version, items,
                                        lambda verse: verse.text,
                                        training_text, ref=ref, missing_only=missing_only,
                                        thesaurus=thesaurus)

    elif version.text_type == TextType.CATECHISM:
        items = list(version.qapairs.all())
        if is_done(items):
            return

        training_text = ' '.join(p.question + " " + p.answer for p in items)
        generate_suggestions_helper(version, items,
                                    lambda qapair: qapair.answer,
                                    training_text,
                                    ref=ref, missing_only=missing_only,
                                    thesaurus=thesaurus)


def build_markov_chains_with_sentence_breaks(training_text, size):
    # Look in dict first
    hash = hashlib.sha1(training_text).hexdigest()
    if (hash, size) in MARKOV_CHAINS:
        return MARKOV_CHAINS[hash, size]

    sentences = training_text.split(".")
    v_accum, c_accum = pykov.maximum_likelihood_probabilities([])
    for i, s in enumerate(sentences):
        print "Analysing sentence %d" % i
        if not s:
            continue
        words = split_into_words_for_suggestions(s)
        if size == 1:
            chain_input = words
        else:
            chain_input = [tuple(words[i:i+size]) for i in range(0, len(words)-(size-1))]
        v, c = pykov.maximum_likelihood_probabilities(chain_input, lag_time=1)
        c_accum += c

    MARKOV_CHAINS[hash, size] = c_accum
    return c_accum


def generate_suggestions_helper(version, items, text_getter, training_text, ref=None,
                                missing_only=True, thesaurus=None):
    first_words = sentence_first_words(training_text)
    first_word_frequencies = frequency_pairs(first_words)

    markov_chains = {}

    def get_markov_chain(size):
        if size in markov_chains:
            return markov_chains[size]
        else:
            c = build_markov_chains_with_sentence_breaks(training_text, size)
            markov_chains[size] = c
            return c

    def suggestions_thesaurus(words, i, count):
        # Don't fill up with thesaurus answers, sometimes they are dumb,
        # so limit to MIN_SUGGESTIONS
        return [(w, 1.0) for w in thesaurus.get(words[i], [])][:MIN_SUGGESTIONS][:count]

    def suggestions_first_word(words, i, count):
        return first_word_frequencies[:]

    def mk_suggestions_markov(size):
        def suggestions_markov(words, i, count):
            correct_word = words[i]
            if size == 1:
                start = words[i-1]
            else:
                start = tuple(words[i-size:i])
            chain = get_markov_chain(size)
            options = chain.succ(start).items()
            # We filter out the correct word, so that we know how many
            # alternatives we have, and so probabilities for other
            # words aren't skewed.
            return [(w, f) for w, f in options if w != correct_word]
        return suggestions_markov

    def suggestions_random(words, i, count):
        retval = []
        correct_word = words[i]
        while len(retval) < count:
            s = random.choice(words)
            if s != correct_word:
                retval.append((s, 1.0))
        return retval

    MIN_SUGGESTIONS = 30
    MAX_SUGGESTIONS = 50

    # Strategies for finding alternatives, ordered according to how good they will be
    strategies = []
    if thesaurus is not None:
        strategies.append(
            # Thesaurus isn't always very good, because
            # it can come up with some dumb suggestions.
            (lambda i: True, suggestions_thesaurus, 1)
        )

    strategies.extend([
        (lambda i: i == 0, suggestions_first_word, 4),
        (lambda i: i > 2, mk_suggestions_markov(3), 4),
        (lambda i: i > 1, mk_suggestions_markov(2), 4),
        (lambda i: i > 0, mk_suggestions_markov(1), 4),
        (lambda i: True, suggestions_random, 4),
    ])

    to_create = []
    for item in items:
        if ref is not None and item.reference != ref:
            continue

        text = text_getter(item)
        words = split_into_words_for_suggestions(text)

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
        for i, word in enumerate(words):
            relevance = 1.0
            word_suggestions = []
            for condition, method, scale_factor in strategies:
                if condition(i):
                    need = MIN_SUGGESTIONS - len(word_suggestions) # Only last strategy really uses this
                    new_suggestions = scale_suggestions(method(words, i, need), relevance)
                    if len(new_suggestions) > 0:
                        word_suggestions = merge_suggestions(word_suggestions, new_suggestions)
                        relevance = relevance / scale_factor # scale down worse methods for finding suggestions

            word_suggestions.sort(key=lambda (a,b): -b)
            word_suggestions = scale_suggestions(word_suggestions[0:MAX_SUGGESTIONS])

            # Add hits=0
            item_suggestions.append([(w,f,0) for w,f in word_suggestions])

        to_create.append(WordSuggestionData(version=version,
                                            reference=item.reference,
                                            suggestions=item_suggestions,
                                            hash=hashlib.sha1(text),
                                        ))

    WordSuggestionData.objects.bulk_create(to_create)


def scale_suggestions(suggestions, factor=1.0):
    # Scale frequencies to maxium of factor
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
    for wd in get_in_batches(WordSuggestionData.objects.filter(version__slug=version_name)):
        for p in wd.get_suggestion_pairs():
            s |= set(w for w,f in p)
    return s


def get_all_version_words(version_name):
    s = set()
    for verse in get_in_batches(Verse.objects.filter(version__slug=version_name)):
        s |= set(split_into_words_for_suggestions(verse.text))

    for qapair in get_in_batches(QAPair.objects.filter(catechism__slug=version_name)):
        s |= set(split_into_words_for_suggestions(qapair.answer))
    return s
