import re

import attr
from parsy import ParseError, char_from, generate, regex, string, string_from, whitespace

from learnscripture.ftl_bundles import t
from learnscripture.utils.cache import memoize_function

from .books import (
    get_bible_book_abbreviation_map,
    get_bible_book_name,
    get_bible_book_number,
    get_bible_books,
    is_single_chapter_book,
)
from .constants import BIBLE_BOOK_INFO
from .languages import LANGUAGE_CODE_INTERNAL, normalize_reference_input


@attr.s
class ParsedReference:
    language_code = attr.ib()
    book_name = attr.ib()  # Always canonical form
    start_chapter = attr.ib()
    start_verse = attr.ib()
    end_chapter = attr.ib(default=None)
    end_verse = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.book_number = get_bible_book_number(self.language_code, self.book_name)
        self.internal_book_name = get_bible_book_name(LANGUAGE_CODE_INTERNAL, self.book_number)

        # Normalize to a form where every ParsedReference is potentially a
        # range. This means we can treat ranges and single verses uniformly.
        if self.start_chapter is None and is_single_chapter_book(self.book_number):
            self.start_chapter = 1
            self.end_chapter = 1
        if self.end_chapter is None:
            self.end_chapter = self.start_chapter
        if self.end_verse is None:
            self.end_verse = self.start_verse
        if self.end_chapter is not None:
            if self.end_chapter < self.start_chapter:
                raise InvalidVerseReference(
                    t(
                        "bibleverses-invalid-reference-end-chapter-before-start-chapter",
                        dict(end=self.end_chapter, start=self.start_chapter),
                    )
                )
            if self.end_chapter == self.start_chapter:
                if self.end_verse is not None:
                    if self.end_verse < self.start_verse:
                        raise InvalidVerseReference(
                            t(
                                "bibleverses-invalid-reference-end-verse-before-start-verse",
                                dict(end=self.end_verse, start=self.start_verse),
                            )
                        )
        if self.start_chapter is not None and self.start_chapter == self.end_chapter:
            if (
                self.start_verse == 1
                and self.start_chapter in self.book_info["verse_counts"]
                and self.end_verse == self.book_info["verse_counts"][self.start_chapter]
            ):
                self.start_verse = None
                self.end_verse = None

    def canonical_form(self):
        # Reverse of bible_reference_strict
        retval = self.book_name
        if self.start_chapter is not None:
            retval += f" {self.start_chapter}"
            if self.start_verse is not None:
                retval += f":{self.start_verse}"
                if self.end_chapter != self.start_chapter:
                    assert self.end_verse is not None
                    retval += f"-{self.end_chapter}:{self.end_verse}"
                elif self.end_verse != self.start_verse:
                    retval += f"-{self.end_verse}"
        return retval

    def _clone(self, **kwargs):
        return attr.evolve(self, **kwargs)

    def translate_to(self, language_code):
        return self._clone(
            language_code=language_code,
            book_name=get_bible_book_name(language_code, self.book_number),
        )

    def to_internal(self):
        return self.translate_to(LANGUAGE_CODE_INTERNAL)

    @classmethod
    def from_start_and_end(cls, start_parsed_ref, end_parsed_ref):
        if start_parsed_ref.language_code != end_parsed_ref.language_code:
            raise InvalidVerseReference(f"Language {start_parsed_ref.language_code} != {end_parsed_ref.language_code}")
        if start_parsed_ref.book_name != end_parsed_ref.book_name:
            raise InvalidVerseReference(f"Book {start_parsed_ref.book_name} != {end_parsed_ref.book_name}")

        return cls(
            language_code=start_parsed_ref.language_code,
            book_name=start_parsed_ref.book_name,
            start_chapter=start_parsed_ref.start_chapter,
            start_verse=start_parsed_ref.start_verse,
            end_chapter=end_parsed_ref.end_chapter,
            end_verse=end_parsed_ref.end_verse,
        )

    def is_whole_book(self):
        return self.start_chapter is None or (is_single_chapter_book(self.book_number) and self.start_verse is None)

    def is_whole_chapter(self):
        return self.start_chapter is not None and self.start_verse is None

    def whole_book_prefix(self):
        """
        Returns a prefix string that matches all the verses in the book
        """
        return self.book_name + " "

    def is_single_verse(self):
        return (
            self.start_verse is not None
            and self.end_chapter == self.start_chapter
            and self.end_verse == self.start_verse
        )

    def is_in_bounds(self):
        book_info = self.book_info
        chapter_count = book_info["chapter_count"]
        if self.is_whole_book():
            return True
        if self.start_chapter < 1:
            return False
        if self.start_chapter > chapter_count or self.end_chapter > chapter_count:
            return False
        for chapter, verse in [(self.start_chapter, self.start_verse), (self.end_chapter, self.end_verse)]:
            verse_count = book_info["verse_counts"][chapter]
            if verse is None:
                # implies beginning/end of chapter, in bounds by definitions
                continue
            if verse > verse_count:
                return False
        return True

    def get_start(self):
        if self.is_single_verse():
            return self
        else:
            start_chapter = self.start_chapter
            if start_chapter is None:
                start_chapter = 1
            start_verse = self.start_verse
            if start_verse is None:
                start_verse = 1
            return self._clone(
                start_chapter=start_chapter, start_verse=start_verse, end_chapter=start_chapter, end_verse=start_verse
            )

    def get_end(self):
        if self.is_single_verse():
            return self
        else:
            end_chapter = self.end_chapter
            if end_chapter is None:
                end_chapter = self.book_info["chapter_count"]
            end_verse = self.end_verse
            if end_verse is None:
                end_verse = self.book_info["verse_counts"][end_chapter]
            return self._clone(
                start_chapter=end_chapter, start_verse=end_verse, end_chapter=end_chapter, end_verse=end_verse
            )

    @property
    def book_info(self):
        return BIBLE_BOOK_INFO[self.internal_book_name]

    def to_list(self):
        """
        From a ParsedReference that may span more than one verse,
        return a list of all ParsedReference in the range.
        """
        start_ref = self.get_start()
        end_ref = self.get_end()
        assert start_ref.book_number == end_ref.book_number
        book_info = self.book_info
        assert start_ref.start_chapter <= end_ref.start_chapter
        if start_ref.start_chapter == end_ref.start_chapter:
            assert start_ref.start_verse <= end_ref.start_verse

        results = []
        current_ref = start_ref
        while True:
            results.append(current_ref)
            # Next verse
            next_ref = current_ref
            verse_num = next_ref.start_verse + 1
            next_ref = attr.evolve(next_ref, start_verse=verse_num, end_verse=verse_num)
            verses_in_chapter = book_info["verse_counts"][next_ref.start_chapter]
            if next_ref.start_verse > verses_in_chapter:
                chapter_num = next_ref.start_chapter + 1
                verse_num = 1
                next_ref = attr.evolve(
                    next_ref,
                    start_chapter=chapter_num,
                    end_chapter=chapter_num,
                    start_verse=verse_num,
                    end_verse=verse_num,
                )
            if next_ref.start_chapter > end_ref.start_chapter:
                break
            if next_ref.start_chapter == end_ref.start_chapter and next_ref.start_verse > end_ref.start_verse:
                break
            current_ref = next_ref
        return results


class InvalidVerseReference(ValueError):
    pass


# Generic parsing utilities


def dict_map(d):
    """
    Returns a parser that matches any key from the dict,
    and return the corresponding value for that key.
    """
    return string_from(*d.keys()).map(lambda v: d[v])


# Specific parsing components


@memoize_function
def book_strict(language_code):
    """
    Returns a parser for a Bible book, strict mode (canonical only)
    """
    return string_from(*get_bible_books(language_code))


@memoize_function
def book_loose(language_code):
    """
    Returns a parser for a Bible book, loose mode.
    """
    return dict_map(get_bible_book_abbreviation_map(language_code)).desc(f"Expected Bible book in {language_code}")


number = regex(r"[0-9]+").map(int)
chapter = number.desc("chapter number [0-9]+")
verse = number.desc("verse number [0-9]+")

verse_range_sep = string("-") | string("–")  # '\u2013'
chapter_verse_sep = string(":")
chapter_verse_sep_loose = char_from(":v.").result(":")

# To avoid the work of creating Parser objects within bible_reference_strict or
# bible_reference_loose, we create as much as possible at this scope where we
# can reuse it. We also put `memoize_function` on some functions above.

optional_whitespace = whitespace.optional()
optional_space = string(" ").optional()
optional_chapter_verse_sep = chapter_verse_sep.optional()
optional_verse_range_sep = verse_range_sep.optional()
optional_chapter_verse_sep_loose = chapter_verse_sep_loose.optional()
optional_chapter = chapter.optional()
verse_or_chapter = verse | chapter


def bible_reference_parser_for_lang(language_code: str, strict: bool) -> ParsedReference:
    """
    Returns a Bible reference parser for the language.

    If strict=True, then only canonical references are allowed.
    Otherwise looser checks are done, but it is assumed
    that the input is already case normalized.
    """

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
                end_verse=end_verse,
            )

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
                end_verse=end_verse,
            )

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
        raise InvalidVerseReference(f"Could not parse '{localized_reference}' as bible reference - {str(e)}")


def parse_validated_internal_reference(internal_reference):
    return parse_validated_localized_reference(LANGUAGE_CODE_INTERNAL, internal_reference)


def parse_unvalidated_localized_reference(
    language_code, localized_reference, allow_whole_book=True, allow_whole_chapter=True
):
    """
    Parse user input as a Bible reference, returning a ParsedReference
    Returns None if it doesn't look like a reference (doesn't parse),
    or raises InvalidVerseReference if it does but isn't correct
    (for example, if the chapter/verse numbers are out of valid range)

    If allow_whole_chapter==False, will return None for
    references that are whole chapters.

    If allow_whole_book==False, will return None for
    references that are entire books

    This is used by higher level code that deals with unvalidated user input.
    """
    q = normalize_reference_input(language_code, localized_reference)
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


def parse_passage_title_partial_loose(language_code, title):
    """
    If possible, parse the initial part of a title as a bible reference,
    returning (parsed_ref,
               boolean that is True for a complete parse with no remainder, False otherwise)
    or        (None, False)
    """
    title_norm = normalize_reference_input(language_code, title)
    try:
        parsed_ref, remainder = bible_reference_parser_for_lang(language_code, False).parse_partial(title_norm)
    except (ParseError, InvalidVerseReference):
        return None, False

    # We expect the remainder to be empty or to start with punctuation i.e. non
    # alphanumeric. Otherwise it is a mistake to think the first part was a
    # bible reference.
    if len(remainder) > 0:
        if re.match(r"\w", remainder[0]):
            return None, False

    # For use cases of this function, we always want to allow whole books/chapters, so
    # don't put limits here.

    # We don't return the remainder itself - it's useless because it has been
    # mangled by normalize_reference_input.
    return parsed_ref, (len(remainder.strip()) == 0)


def localize_internal_reference(language_code, internal_reference):
    return parse_validated_internal_reference(internal_reference).translate_to(language_code).canonical_form()


def internalize_localized_reference(language_code, localized_reference):
    return parse_validated_localized_reference(language_code, localized_reference).to_internal().canonical_form()


def parse_break_list(breaks):
    """
    Parse a break list, which is a comma separated list of internal references, or raise a ValueError for failure.
    """
    # breaks is a common separated list of internal references, created in create.js
    try:
        return (bible_reference_parser_for_lang(LANGUAGE_CODE_INTERNAL, True).sep_by(string(","))).parse(breaks)

    except ParseError:
        raise ValueError(f"'{breaks}' is not a valid list of internal Bible references")
