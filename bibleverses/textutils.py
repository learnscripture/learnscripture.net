import re

ALPHANUMERIC_RE = re.compile(r'\w')
WORD_SPLITTER = re.compile(r'( |\n)')


def is_punctuation(text):
    return not ALPHANUMERIC_RE.search(text)


def is_newline(text):
    return text == "\n"


def split_into_words(text, fix_punctuation_whitespace=True):
    """
    Splits text into series of words. Punctuation and newlines are left in
    place.

    If fix_punctuation_whitespace==True (the default), then 'words' that consist
    only of punctuation are merged with neighbouring actual words.
    """
    # The result is passed back through client side and used as
    # the text to display and test against. It keeps newlines because
    # they are useful in display.

    # The number of items returned should be the number of words (used for
    # scoring purposes), so punctuation and newlines are kept next to words.

    # This is used by bibleverses.suggestions, therefore needs to match
    # the way that Learn.elm splits words up.

    # We need to cope with things like Gen 3:22
    #    and live forever--"'
    # and Gen 1:16
    #    And God made the two great lights--the greater light
    #
    # and when -- appears with punctuation on one side, we don't
    # want this to end up on its own. Also, text with a single
    # hyphen surrounding by whitespace needs to be handled too.
    t = (text
         .replace('--', ' -- ')
         .replace('\r\n', '\n')
         .strip(" "))
    l = WORD_SPLITTER.split(t)
    # Eliminate spaces
    l = [w for w in l if w not in [" ", ""]]
    # Merge newlines
    l = merge_items_left(l, is_newline)
    if fix_punctuation_whitespace:
        # Merge punctuation-only-items with item to left.
        l = merge_items_left(l, is_punctuation)
        # Then to right e.g. leading quotation marks
        l = merge_items_right(l, is_punctuation)

    return l


def merge_items_left(words, predicate):
    retval = []
    for item in words:
        if predicate(item) and len(retval) > 0:
            retval[-1] += item
        else:
            retval.append(item)
    return retval


def merge_items_right(words, predicate):
    retval = []
    for item in words[::-1]:
        if predicate(item) and len(retval) > 0:
            retval[-1] = item + retval[-1]
        else:
            retval.append(item)
    return retval[::-1]


def count_words(text):
    return len(split_into_words(text))
