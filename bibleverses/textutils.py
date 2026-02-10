import re
from collections.abc import Sequence

from pypinyin import Style, lazy_pinyin

ALPHANUMERIC_RE = re.compile(r"\w")
WORD_SPLITTER = re.compile(r"( |\n)")


def is_punctuation(text):
    return not ALPHANUMERIC_RE.search(text)


def is_newline(text):
    return text == "\n"


def is_chinese_language(language_code: str):
    """Check if language code indicates Chinese (Traditional or Simplified)."""
    return language_code.startswith("zh")


def split_into_words(text: str, *, fix_punctuation_whitespace: bool = True, language_code: str):
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

    # Handle Chinese text with character-by-character splitting
    if is_chinese_language(language_code):
        # For Chinese, treat each character as a word for learning purposes
        # This avoids incorrect word segmentation and makes testing simpler
        t = text.replace("\r\n", "\n").strip(" ")

        # Split by newlines first to preserve them
        lines = t.split("\n")
        words = []

        for i, line in enumerate(lines):
            if line:
                # Split line into individual characters
                for char in line:
                    words.append(char)

            # Add newline back (except after last line)
            if i < len(lines) - 1:
                if words:
                    words[-1] += "\n"
                else:
                    words.append("\n")

        if fix_punctuation_whitespace:
            # Merge punctuation-only items with neighboring words
            words = merge_items_left(words, is_punctuation)
            words = merge_items_right(words, is_punctuation)

        return words

    # Non-Chinese text: use original whitespace-based splitting
    # We need to cope with things like Gen 3:22
    #    and live forever--"'
    # and Gen 1:16
    #    And God made the two great lights--the greater light
    #
    # and when -- appears with punctuation on one side, we don't
    # want this to end up on its own. Also, text with a single
    # hyphen surrounding by whitespace needs to be handled too.
    t = text.replace("--", " -- ").replace("\r\n", "\n").strip(" ")
    words = WORD_SPLITTER.split(t)
    # Eliminate spaces
    words = [w for w in words if w not in [" ", ""]]
    # Merge newlines
    words = merge_items_left(words, is_newline)
    if fix_punctuation_whitespace:
        # Merge punctuation-only-items with item to left.
        words = merge_items_left(words, is_punctuation)
        # Then to right e.g. leading quotation marks, leading ¡ and ¿
        words = merge_items_right(words, is_punctuation)

    return words


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


def count_words(text: str, *, language_code: str):
    return len(split_into_words(text, language_code=language_code))


def chinese_word_to_test_string(word: str):
    """
    Convert a Chinese word to a test string.

    For Chinese characters, returns the Pinyin first letter.
    This supports 'FirstLetter' testing mode.
    Chinese punctuation is stripped from test strings.

    Examples:
        "神" -> "s" (shen -> s)
        "愛" -> "a" (ai -> a)
        "人！" -> "r" (ren -> r, punctuation removed)
    """
    # pypinyin converts Chinese characters to pinyin and leaves non-Chinese
    # characters (like punctuation) as-is
    # Style.NORMAL gives pinyin without tone marks
    pinyin_list = lazy_pinyin(word, style=Style.NORMAL)

    # Common Chinese punctuation marks to strip from test strings
    chinese_punctuation = "，。、；：！？（）【】《》「」『』"

    # Collect test string characters
    test_chars = []

    for i, py in enumerate(pinyin_list):
        if py and len(py) > 0:
            # Check if this is a Chinese character's pinyin (all alphabetic)
            # or punctuation/other (returned as-is by pypinyin)
            if py.isalpha():
                # Mapping back to original word is tricky if pypinyin split differently than chars.
                # But for standard Chinese text, split_into_words has likely already
                # split it into single chars (or short sequences).
                # To be safe, we check if the pinyin looks different from the source
                # OR if the source was Chinese.

                # However, strict mapping index `i` to `word[i]` is only valid if
                # pypinyin output maps 1-to-1 with input chars.
                # lazy_pinyin documentation says it does for Chinese chars.
                # But English words are kept as single items.

                # If we assume `word` is passed from `split_into_words` which splits
                # Chinese into single chars, then `word` is likely 1 char long (plus optional punct).

                # Let's rely on pinyin result.
                test_chars.append(py[0])

            elif py not in chinese_punctuation:
                # It's non-Chinese punctuation - keep as-is
                # (e.g., English punctuation like quotes or dashes)
                test_chars.append(py)
            # Chinese punctuation is skipped (not appended)

    return "".join(test_chars)


def words_to_test_strings(words: Sequence[str], *, language_code: str):
    """
    Convert a list of words to their test strings.

    For Chinese words, converts to pinyin first letters.
    For punctuation-only words, returns empty string (so they're skipped during input).

    Args:
        words: List of word strings
        language_code: Language code (e.g., 'zh-Hant' for Traditional Chinese)

    Returns:
        List of test strings (same length as input)
    """
    if not is_chinese_language(language_code):
        # Non-Chinese: words are their own test strings
        return words

    result = []
    for word in words:
        # Strip whitespace to check the actual content
        word_stripped = word.rstrip("\n").strip()

        if is_punctuation(word_stripped) or word_stripped == "":
            # Punctuation-only or empty: return the word as-is for display
            # but frontend will skip it because it has no alphanumeric characters
            result.append(word)
        else:
            # Convert Chinese word to pinyin first letters
            test_str = chinese_word_to_test_string(word_stripped)
            # Preserve trailing newline if present
            if word.endswith("\n"):
                test_str += "\n"
            result.append(test_str)
    return result
