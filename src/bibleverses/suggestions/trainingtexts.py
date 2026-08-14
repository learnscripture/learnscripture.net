# Training texts:
import logging

from bibleverses.models import TextVersion

from .constants import ALL_TEXT, similar_books
from .exceptions import LoadingNotAllowed

logger = logging.getLogger(__name__)


class TrainingTexts:
    """
    Dictionary like storage object that represents training texts
    and returns them (lazily) if needed.

    The keys always include TextVersion slug, so that even for different
    TrainingTexts objects the keys are unique.

    The classes are designed so that they can be used if the TextVersion
    object is not passed in. In this case they are only used for their
    list of keys, and the text slug, to identify a set of training text
    that is used by an analysis.
    """

    def __init__(self, text_version: TextVersion | None = None, text_slug: str | None = None, disallow_loading=False):
        self._keys = []
        self._values = {}
        self.text_version: TextVersion | None = text_version
        if text_version is not None:
            text_slug = text_version.slug
        self.text_slug: str = text_slug
        self.disallow_loading = disallow_loading or (text_version is None)

    def __getitem__(self, key) -> str:
        text_slug, _ = key
        assert text_slug == self.text_slug
        if key not in self._keys:
            raise LookupError(key)
        if key not in self._values:
            retval = self.lookup(key)
            self._values[key] = retval
        return self._values[key]

    def keys(self):
        return self._keys[:]

    def values(self):
        return [self[k] for k in self.keys()]

    def lookup(self, key) -> str:
        raise NotImplementedError()


class BibleTrainingTexts(TrainingTexts):
    def __init__(self, books=None, text_version=None, **kwargs):
        super().__init__(text_version=text_version, **kwargs)
        all_books = []
        for book in books:
            for b in similar_books(book, text_version.language_code):
                if b not in all_books:
                    all_books.append(b)
        self._keys = [(self.text_slug, b) for b in all_books]

    def lookup(self, key) -> str:
        if self.disallow_loading:
            raise LoadingNotAllowed(key)
        version_slug, book = key
        logger.info(f"Retrieving {self.text_slug}: {book}")
        from bibleverses.suggestions.modelapi import get_whole_book

        return get_whole_book(book, self.text_version).text


class CatechismTrainingTexts(TrainingTexts):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._keys = [(self.text_slug, ALL_TEXT)]

    def lookup(self, key) -> str:
        if self.disallow_loading:
            raise LoadingNotAllowed(key)
        logger.info(f"Retrieving {self.text_version.slug}")
        items = list(self.text_version.qapairs.all())
        return " ".join(p.question + " " + p.answer for p in items)
