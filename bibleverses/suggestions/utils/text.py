import re

from bibleverses.textutils import is_punctuation, split_into_words

PUNCTUATION = "!?,.<>()[];:\"'-–+"
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


def normalize_word(word):
    word = word.strip(PUNCTUATION_OR_WHITESPACE)
    return word.lower()


def split_into_words_for_suggestions(text):
    return list(map(normalize_word, split_into_words(text)))


def split_into_sentences(text):
    return [s for s in [s.strip(PUNCTUATION_OR_WHITESPACE) for s in text.split('.')]
            if s]


def sentence_first_words(text):
    return [split_into_words_for_suggestions(l)[0]
            for l in split_into_sentences(text)]
