import attr
from parsy import alt, generate, regex, string, whitespace, ParseError

from learnscripture.utils.cache import memoize_function

from .books import get_bible_book_number, get_bible_books, get_bible_book_abbreviation_map, is_single_chapter_book
from .languages import normalize_search_input


@attr.s
class ParsedReference(object):
    language_code = attr.ib()
    book_name = attr.ib()  # Always canonical form
    start_chapter = attr.ib()
    start_verse = attr.ib()
    end_chapter = attr.ib(default=None)
    end_verse = attr.ib(default=None)

    def __attrs_post_init__(self):
        # Normalize to a form where every ParsedReference is potentially a
        # range. This means we can treat ranges and single verses uniformly.
        if is_single_chapter_book(self.book_number):
            self.start_chapter = 1
        if self.end_chapter is None:
            self.end_chapter = self.start_chapter
        if self.end_verse is None:
            self.end_verse = self.start_verse
        if self.end_chapter is not None:
            if self.end_chapter < self.start_chapter:
                raise InvalidVerseReference("end chapter {0} is before start chapter {1}"
                                            .format(self.end_chapter, self.start_chapter))
            if self.end_chapter == self.start_chapter:
                if self.end_verse is not None:
                    if self.end_verse < self.start_verse:
                        raise InvalidVerseReference("end verse {0} is before start verse {1}"
                                                    .format(self.end_verse, self.start_verse))

    def canonical_form(self):
        # Reverse of bible_reference_strict
        retval = self.book_name
        if self.start_chapter is not None:
            retval += " {0}".format(self.start_chapter)
            if self.start_verse is not None:
                retval += ":{0}".format(self.start_verse)
                if self.end_chapter != self.start_chapter:
                    assert self.end_verse is not None
                    retval += "-{0}:{1}".format(self.end_chapter, self.end_verse)
                elif self.end_verse != self.start_verse:
                    retval += "-{0}".format(self.end_verse)
        return retval

    @classmethod
    def from_start_and_end(cls, start, end):
        return cls(language_code=start.language_code,
                   book_name=start.book_name,
                   start_chapter=start.start_chapter,
                   start_verse=start.start_verse,
                   end_chapter=end.end_chapter,
                   end_verse=end.end_verse)

    @property
    def book_number(self):
        return get_bible_book_number(self.language_code, self.book_name)

    def is_whole_book(self):
        return (self.start_chapter is None or
                (is_single_chapter_book(self.book_number) and
                 self.start_verse is None))

    def is_whole_chapter(self):
        return self.start_chapter is not None and self.start_verse is None

    def is_single_verse(self):
        return (self.start_verse is not None and
                self.end_chapter == self.start_chapter and
                self.end_verse == self.start_verse)

    def get_start(self):
        if self.is_single_verse():
            return self
        else:
            return ParsedReference(
                language_code=self.language_code,
                book_name=self.book_name,
                start_chapter=self.start_chapter,
                start_verse=self.start_verse)

    def get_end(self):
        if self.is_single_verse():
            return self
        else:
            return ParsedReference(
                language_code=self.language_code,
                book_name=self.book_name,
                start_chapter=self.end_chapter,
                start_verse=self.end_verse)


class InvalidVerseReference(ValueError):
    pass


# Generic parsing utilities

def oneof_strings(strings):
    """
    Returns a parser that matches any of the passed in strings
    """
    # Sort longest first, so that backtracking works correctly
    return alt(*map(string, sorted(strings, key=lambda s: -len(s))))


def dict_map(d):
    """
    Returns a parser that matches any key from the dict,
    and return the corresponding value for that key.
    """
    return oneof_strings(d.keys()).map(lambda v: d[v])


def optional(parser):
    """
    Returns a parser that optional matches the
    passed in parser, or returns None
    """
    return parser.times(0, 1).map(lambda v: v[0] if v else None)


# Specific parsing components

@memoize_function
def book_strict(language_code):
    """
    Returns a parser for a Bible book, strict mode (canonical only)
    """
    books = get_bible_books(language_code)
    return oneof_strings(books).desc("|".join(books))


@memoize_function
def book_loose(language_code):
    """
    Returns a parser for a Bible book, loose mode.
    """
    return (dict_map(get_bible_book_abbreviation_map(language_code))
            .desc("Expected Bible book in {0}".format(language_code)))


number = regex(r'[0-9]+').map(int)
chapter = number.desc("chapter number [0-9]+")
verse = number.desc("verse number [0-9]+")

verse_range_sep = string("-")
chapter_verse_sep = string(":")
chapter_verse_sep_loose = oneof_strings([":", "v", "."]).result(":")

# To avoid the work of creating Parser objects within bible_reference_strict or
# bible_reference_loose, we create as much as possible at this scope where we
# can reuse it. We also put `memoize_function` on some functions above.

optional_whitespace = optional(whitespace)
optional_space = optional(string(" "))
optional_chapter_verse_sep = optional(chapter_verse_sep)
optional_verse_range_sep = optional(verse_range_sep)
optional_chapter_verse_sep_loose = optional(chapter_verse_sep_loose)
optional_chapter = optional(chapter)
verse_or_chapter = verse | chapter


def bible_reference_parser_for_lang(language_code, strict):
    # Bible references look something like:
    # Genesis
    # Genesis 1
    # Genesis 1:2
    # Genesis 1:2-3
    # Genesis 1:2-4:5

    # This currently holds true for the languages we support, just with
    # different book names.
    if strict:
        @generate
        def bible_reference_strict():
            start_chapter, start_verse, end_chapter, end_verse = None, None, None, None
            book_name = yield book_strict(language_code)
            break1 = yield optional_space
            if break1 is not None:
                start_chapter = yield chapter
                sep1 = yield optional_chapter_verse_sep
                if sep1 is not None:
                    start_verse = yield verse
                    sep2 = yield optional_verse_range_sep
                    if sep2 is not None:
                        # Don't know if it is verse or chapter yet
                        v_or_c = yield verse_or_chapter
                        sep3 = yield optional_chapter_verse_sep
                        if sep3 is None:
                            end_verse = v_or_c
                        else:
                            end_chapter = v_or_c
                            end_verse = yield verse

            return ParsedReference(
                language_code=language_code,
                book_name=book_name,
                start_chapter=start_chapter,
                start_verse=start_verse,
                end_chapter=end_chapter,
                end_verse=end_verse)

        return bible_reference_strict
    else:
        # Very similar to above, but with more optional whitespace and several
        # looser checks.
        @generate
        def bible_reference_loose():
            start_chapter, start_verse, end_chapter, end_verse = None, None, None, None
            yield optional_whitespace
            book_name = yield book_loose(language_code)
            break1 = yield optional_whitespace
            if break1 is not None:
                start_chapter = yield optional_chapter
                yield optional_whitespace
                if start_chapter is not None:
                    sep1 = yield optional_chapter_verse_sep_loose
                    yield optional_whitespace
                    if sep1 is not None:
                        start_verse = yield verse
                        yield optional_whitespace
                        sep2 = yield optional_verse_range_sep
                        if sep2 is not None:
                            yield optional_whitespace
                            # Don't know if it is verse or chapter yet
                            v_or_c = yield verse_or_chapter
                            yield optional_whitespace
                            sep3 = yield optional_chapter_verse_sep_loose
                            if sep3 is None:
                                end_verse = v_or_c
                            else:
                                end_chapter = v_or_c
                                yield optional_whitespace
                                end_verse = yield verse
            yield optional_whitespace

            return ParsedReference(
                language_code=language_code,
                book_name=book_name,
                start_chapter=start_chapter,
                start_verse=start_verse,
                end_chapter=end_chapter,
                end_verse=end_verse)

        return bible_reference_loose


def parse_validated_localized_reference(language_code, localized_reference):
    """
    Parse a validated reference, returning a ParsedReference
    Raises InvalidVerseReference if there is any error.

    (Exceptions shouldn't happen, this function should be used only
    for Bible references that already conform to the correct
    format).
    """
    try:
        return bible_reference_parser_for_lang(language_code, True).parse(localized_reference)
    except ParseError as e:
        raise InvalidVerseReference(
            "Could not parse '{0}' as bible reference - {1}".format(
                localized_reference,
                str(e)))


def parse_unvalidated_localized_reference(language_code, localized_reference,
                                          allow_whole_book=True, allow_whole_chapter=True):
    """
    Parse user input as a Bible reference, returning a ParsedReference
    Returns None if it doesn't look like a reference (doesn't parse),
    or raises InvalidVerseReference if it does but isn't correct.

    If allow_whole_chapter==False, will return None for
    references that are whole chapters.

    If allow_whole_book==False, will return None for
    references that are entire books

    This is used by higher level code that deals with unvalidated user input.
    """
    q = normalize_search_input(language_code, localized_reference)
    try:
        parsed_ref = bible_reference_parser_for_lang(language_code, False).parse(q)
    except ParseError:
        # This doesn't look like a bible reference at all.
        return None
    if not allow_whole_chapter and parsed_ref.is_whole_chapter():
        return None
    if not allow_whole_book and parsed_ref.is_whole_book():
        if parsed_ref.is_whole_chapter() and allow_whole_chapter:
            # Single chapter books - the book is both a single chapter and a
            # book - we allow this.
            pass
        else:
            return None
    return parsed_ref


def parse_break_list(language_code, breaks, first_verse=None):
    """
    Parse a comman separated list of references, or raise a ValueError for failure.
    """
    # breaks is a common separated list of references, created in create.js
    bible_ref = bible_reference_parser_for_lang(language_code, True)
    bible_ref_list = bible_ref.sep_by(string(","), min=1)
    parser = bible_ref_list
    if first_verse is not None:
        # Legacy format
        legacy_break_list = ((regex("[0-9]+").map(int)
                              .sep_by(string(":"), min=1, max=2))
                             .sep_by(string(",")))
        parser = parser | legacy_break_list
    try:
        ref_list = parser.parse(breaks)
        if first_verse is not None:
            # legacy processing
            retval = []
            first_parsed_ref = parse_validated_localized_reference(language_code,
                                                                   first_verse.localized_reference)
            current_chapter = first_parsed_ref.start_chapter
            current_verse = first_parsed_ref.start_verse
            for item in ref_list:
                if isinstance(item, ParsedReference):
                    retval.append(item)
                else:
                    assert isinstance(item, list)
                    if len(item) == 1:
                        # Verse number
                        current_verse = item[0]
                    else:
                        current_chapter, current_verse = item
                    new_item = ParsedReference(language_code=language_code,
                                               book_name=first_parsed_ref.book_name,
                                               start_chapter=current_chapter,
                                               start_verse=current_verse)
                    retval.append(new_item)
            return retval
        else:
            return ref_list

    except ParseError as e:
        raise ValueError("'{0}' is not a valid list of Bible references in language {1}"
                         .format(breaks, language_code))
