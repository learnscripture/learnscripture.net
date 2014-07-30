from collections import Counter
import random
import re

import pykov

from bibleverses.models import get_whole_book, TextType, BIBLE_BOOKS, WordSuggestionData, split_into_words, is_punctuation

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
    return [l.split()[0] for l in [normalise_word(l.strip()) for l in text.split('.')] if l]


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

def frequency_pairs(words):
    return scale_suggestions(Counter(words).items())


def generate_suggestions(version, ref=None, missing_only=True):
    def is_done(items):
        if missing_only:
            references = [item.reference for item in items]
            if version.word_suggestion_data.filter(reference__in=references).count() == len(references):
                # All done
                print "Skipping %s %s" % (version.slug, ' '.join(references))
                return True

    if version.text_type == TextType.BIBLE:
        for book in BIBLE_BOOKS:
            items = get_whole_book(book, version).verses
            if is_done(items):
                continue
            training_text = " ".join(get_whole_book(b, version).text for b in similar_books(book))
            generate_suggestions_helper(version, items,
                                        lambda verse: verse.text,
                                        training_text, ref=ref, missing_only=missing_only)

    elif version.text_type == TextType.CATECHISM:
        items = list(version.qapairs.all())
        if is_done(items):
            return

        training_text = ' '.join(p.question + " " + p.answer for p in items)
        generate_suggestions_helper(version, items,
                                    lambda qapair: qapair.answer,
                                    training_text,
                                    ref=ref, missing_only=missing_only)


def generate_suggestions_helper(version, items, text_getter, training_text, ref=None, missing_only=True):
    first_words = sentence_first_words(training_text)
    first_word_frequencies = frequency_pairs(first_words)

    chain_1 = split_into_words_for_suggestions(training_text)
    p1, P1 = pykov.maximum_likelihood_probabilities(chain_1, lag_time=1)

    chain_2 = [tuple(chain_1[i:i+2]) for i in range(0, len(chain_1)-1)]
    p2, P2 = pykov.maximum_likelihood_probabilities(chain_2, lag_time=1)

    chain_3 = [tuple(chain_1[i:i+3]) for i in range(0, len(chain_1)-2)]
    p3, P3 = pykov.maximum_likelihood_probabilities(chain_3, lag_time=1)

    def suggestions_first_word(words, i, count):
        return first_word_frequencies[:]

    def suggestions_markov_1(words, i, count):
        # Use 1 word chain
        correct_word = words[i]
        start = words[i-1]
        options = P1.succ(start).items()
        # We filter out the correct word, so that we know how many
        # alternatives we have, and so probabilities for other
        # words aren't skewed.
        return [(w, f) for w, f in options if w != correct_word]

    def suggestions_markov_2(words, i, count):
        # Use 2 word chain
        correct_word = words[i]
        start = tuple(words[i-2:i])
        options = P2.succ(start).items()
        return [(w, f) for (p, w), f in options if w != correct_word]

    def suggestions_markov_3(words, i, count):
        # Use 3 word chain
        correct_word = words[i]
        start = tuple(words[i-3:i])
        options = P3.succ(start).items()
        return [(w, f) for (p1, p2, w), f in options if w != correct_word]

    def suggestions_random(words, i, count):
        retval = []
        correct_word = words[i]
        while len(retval) < count:
            s = random.choice(chain_1)
            if s != correct_word:
                retval.append((s, 1.0))
        return retval

    MIN_SUGGESTIONS = 30
    MAX_SUGGESTIONS = 40


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
            factor = 1.0
            word_suggestions = []
            strategies = [
                # Ordered according to how good they will be
                (lambda i: i == 0, suggestions_first_word),
                (lambda i: i > 2, suggestions_markov_3),
                (lambda i: i > 1, suggestions_markov_2),
                (lambda i: i > 0, suggestions_markov_1),
                (lambda i: True, suggestions_random),
            ]
            for condition, method in strategies:
                if len(word_suggestions) < MIN_SUGGESTIONS and condition(i):
                    need = MIN_SUGGESTIONS - len(word_suggestions)
                    new_suggestions = scale_suggestions(method(words, i, need), factor)
                    word_suggestions = merge_suggestions(word_suggestions, new_suggestions)
                    factor = factor / 4 # scale down worse methods for finding suggestions

            word_suggestions.sort(key=lambda (a,b): -b)
            word_suggestions = scale_suggestions(word_suggestions[0:MAX_SUGGESTIONS])

            # Add hits=0
            item_suggestions.append([(w,f,0) for w,f in word_suggestions])

        to_create.append(WordSuggestionData(version=version,
                                            reference=item.reference,
                                            suggestions=item_suggestions))

    WordSuggestionData.objects.bulk_create(to_create)


def scale_suggestions(suggestions, factor=1.0):
    # Scale frequencies to maxium of factor
    if len(suggestions) == 0:
        return suggestions
    max_f = max(f for w, f in suggestions)
    return [(w, float(f)/max_f * factor) for w, f in suggestions]


def merge_suggestions(s1, s2):
    return (Counter(dict(s1)) + Counter(dict(s2))).items()


def get_in_batches(qs, batch_size=100):
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
