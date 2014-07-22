from collections import Counter
import random

import pykov

from bibleverses.models import get_whole_book, WordSuggestion

def normalise_word(word):
    for p in "\"'?!,:;-.()[]": # TODO - apostophes in the middle of word?
        word = word.replace(p, "")
    return word.lower().strip()


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

def split_into_words_for_suggestions(text):
    text = text.replace('--', '-- ')
    return [w for w in [normalise_word(w) for w in text.strip().split()]
            if w]

def frequency_pairs(words):
    return scale_suggestions(Counter(words).items())


def generate_suggestions(book, version, ref=None, missing_only=True):
    book_contents = get_whole_book(book, version)

    training_text = " ".join(get_whole_book(b, version).text for b in similar_books(book))

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

    for verse in book_contents.verses:
        if ref is not None and verse.reference != ref:
            continue

        words = split_into_words_for_suggestions(verse.text)

        # Clear out old suggestions
        existing = version.word_suggestions.filter(reference=verse.reference)
        if missing_only:
            # If first and last exist, assume the rest do.
            if (existing.filter(word_number=0).count() > 0
                and existing.filter(word_number=len(words) - 1).count() > 0):
                print "Skipping %s %s" % (version.slug, verse.reference)
                continue
        else:
            existing.delete()

        verse_suggestions = []
        for i, word in enumerate(words):
            factor = 1.0
            suggestions = []
            strategies = [
                # Ordered according to how good they will be
                (lambda i: i == 0, suggestions_first_word),
                (lambda i: i > 2, suggestions_markov_3),
                (lambda i: i > 1, suggestions_markov_2),
                (lambda i: i > 0, suggestions_markov_1),
                (lambda i: True, suggestions_random),
            ]
            for condition, method in strategies:
                if len(suggestions) < MIN_SUGGESTIONS and condition(i):
                    need = MIN_SUGGESTIONS - len(suggestions)
                    new_suggestions = scale_suggestions(method(words, i, need), factor)
                    suggestions = merge_suggestions(suggestions, new_suggestions)
                    factor = factor / 2

            print "%s %s[%s]" % (version.slug, verse.reference, i)
            suggestions.sort(key=lambda (a,b): -b)
            suggestions = scale_suggestions(suggestions[0:MAX_SUGGESTIONS])

            verse_suggestions.append(suggestions)

        to_create = []
        for word_number, suggestion_list in enumerate(verse_suggestions):
            to_create.extend([WordSuggestion(version=version,
                                             reference=verse.reference,
                                             word=word,
                                             word_number=word_number,
                                             frequency=frequency)
                              for word, frequency in suggestion_list])
        WordSuggestion.objects.bulk_create(to_create)

    return book_contents

def scale_suggestions(suggestions, factor=1.0):
    # Scale frequencies to maxium of factor
    if len(suggestions) == 0:
        return suggestions
    max_f = max(f for w, f in suggestions)
    return [(w, float(f)/max_f * factor) for w, f in suggestions]

def merge_suggestions(s1, s2):
    return (Counter(dict(s1)) + Counter(dict(s2))).items()
