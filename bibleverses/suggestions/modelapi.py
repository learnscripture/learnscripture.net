"""
Word suggestion API for Django model layer code
"""
import gc
import hashlib
import logging

import pyuca
from django.db import transaction

from bibleverses.books import get_bible_book_name, get_bible_book_number, get_bible_books
from bibleverses.models import ComboVerse, TextType, TextVersion, Verse, WordSuggestionData, ensure_text
from bibleverses.services import partial_data_available
from bibleverses.suggestions.utils.text import split_into_words_for_suggestions
from learnscripture.utils.iterators import chunks

from .exceptions import AnalysisMissing
from .generators import SuggestionGenerator
from .storage import AnalysisStorage
from .trainingtexts import BibleTrainingTexts, CatechismTrainingTexts

logger = logging.getLogger(__name__)


COLLATER = pyuca.Collator()


# Normally generate_suggestions is called only by management command, for
# generating in bulk. However, at other times it has been necessary to edit a
# text via the admin, and this triggers 'fix_item' being called to fix up the
# word suggestions.

# See __init__.py for comments about how this code is structured.

# -- Create - for tests only --
def create_word_suggestion_data(
    version=None, version_slug=None, localized_reference=None, hash=None, text=None, suggestions=None, **kwargs
):
    if version_slug is None:
        version_slug = version.slug
    if hash is None:
        hash = hash_text(text)
    return WordSuggestionData.objects.create(
        version_slug=version_slug,
        localized_reference=localized_reference,
        hash=hash,
        suggestions=suggestions,
    )


# -- Fetch --


def word_suggestion_data_qs_for_version(version: TextVersion):
    return WordSuggestionData.objects.filter(version_slug=version.slug)


def get_word_suggestions_by_localized_reference(version, localized_reference) -> list[set[str]]:
    wsds = _get_ordered_word_suggestion_data(version, localized_reference)
    # Now combine:
    retval: list[set[str]] = []
    for wsd in wsds:
        retval.extend(wsd.get_suggestions())
    return retval


def get_word_suggestions_by_localized_reference_bulk(version, localized_reference_list) -> dict[str, list[set[str]]]:
    # Do simple ones in bulk:
    simple_wsds = list(
        word_suggestion_data_qs_for_version(version).filter(localized_reference__in=localized_reference_list)
    )
    s_dict = {w.localized_reference: w.get_suggestions() for w in simple_wsds}
    # Others: (i.e. multi-verse references that span multiple database records
    # in WordSuggestionData). This does O(n) DB queries but hopefully n is small
    # in any given batch.
    for localized_ref in localized_reference_list:
        if localized_ref not in s_dict:
            s_dict[localized_ref] = get_word_suggestions_by_localized_reference(version, localized_ref)
    return s_dict


def _get_ordered_word_suggestion_data(version, localized_reference) -> list[WordSuggestionData]:
    """
    Returns a list of WordSuggestionData for a given localized reference
    (i.e. returning multiple items if the localized_reference is multi-verse)
    """
    localized_references = version.get_localized_reference_list(localized_reference)
    wsds = list(word_suggestion_data_qs_for_version(version).filter(localized_reference__in=localized_references))
    # wsds might not be ordered correctly, we need to re-order
    retval = []
    for localized_ref in localized_references:
        for wsd in wsds:
            if wsd.localized_reference == localized_ref:
                retval.append(wsd)
    return retval


# -- Generate --
def fix_item(version_slug, localized_reference, text_saved):
    version = TextVersion.objects.get(slug=version_slug)
    item = version.get_item_by_localized_reference(localized_reference)
    if getattr(item, "missing", False):
        return  # Doesn't need fixing

    # 'text_saved' is passed through, to ensure that this process (task queue
    # worker) sees the same value that was being saved in the Django process. We
    # can also avoid generating a warning in ensure_text this way.
    if text_saved is not None:
        item.text_saved = text_saved

    # Before recreating, check if the hash has changed. This is especially
    # important for versions where we only partially store locally and have to
    # fetch the data again (triggering a save and this function being called)
    if not item_suggestions_need_updating(item):
        logger.info("Skipping creation of word suggestions for unchanged %s %s", version_slug, localized_reference)
        return

    # To avoid loading large amounts of data over the API,
    # we make it illegal to load any.
    # We are going to have problems fixing the word suggestions, because the
    # current algo assumes access to the whole text. So just log a warning
    disallow_loading = partial_data_available(version_slug)
    try:
        generate_suggestions(
            version,
            missing_only=False,
            localized_reference=localized_reference,
            disallow_loading=disallow_loading,
            text_saved=text_saved,
        )
    except AnalysisMissing as e:
        logger.warning("%r", e.args[0])
        logger.warning(
            "Need to create word suggestions for %s %s but can't because text is not available and saved analysis is not complete",
            version_slug,
            localized_reference,
        )
        return


def item_suggestions_need_updating(item):
    version_slug = item.text_version.slug
    localized_reference = item.localized_reference
    suggestion_data = WordSuggestionData.objects.filter(
        version_slug=version_slug, localized_reference=localized_reference
    ).first()

    if suggestion_data is None:
        return True
    else:
        saved_hash = suggestion_data.hash
        current_hash = hash_text(item.suggestion_text)
        return saved_hash != current_hash


def generate_suggestions(version, localized_reference=None, missing_only=True, disallow_loading=False, text_saved=None):
    analysis_storage = AnalysisStorage()
    language_code = version.language_code
    if version.text_type == TextType.BIBLE:
        if localized_reference is not None:
            v = version.get_verse_list(localized_reference)[0]
            if text_saved is not None:
                v.text_saved = text_saved
            book = get_bible_book_name(language_code, v.book_number)
            items = [v]
            training_texts = BibleTrainingTexts(text_version=version, books=[book], disallow_loading=disallow_loading)
            logger.info("Generating for %s", localized_reference)
            generate_suggestions_for_items(
                analysis_storage,
                version,
                items,
                training_texts,
                localized_reference=localized_reference,
                missing_only=missing_only,
            )
        else:
            for book in get_bible_books(language_code):
                generate_suggestions_for_book(analysis_storage, version, book, missing_only=missing_only)

    elif version.text_type == TextType.CATECHISM:
        training_texts = CatechismTrainingTexts(text_version=version, disallow_loading=disallow_loading)
        items = list(version.qapairs.all())
        if items_all_done(version, items, localized_reference=localized_reference, missing_only=missing_only):
            return

        generate_suggestions_for_items(
            analysis_storage,
            version,
            items,
            training_texts,
            localized_reference=localized_reference,
            missing_only=missing_only,
        )


def generate_suggestions_for_book(analysis_storage, version, localized_book_name: str, missing_only=True):
    logger.info("Generating for %s", localized_book_name)
    items = get_whole_book(localized_book_name, version, ensure_text_present=False).verses
    if items_all_done(version, items, missing_only=missing_only):
        return
    training_texts = BibleTrainingTexts(text_version=version, books=[localized_book_name])
    generate_suggestions_for_items(analysis_storage, version, items, training_texts, missing_only=missing_only)


def generate_suggestions_for_items(
    analysis_storage,
    version,
    items,
    training_texts,
    localized_reference=None,
    missing_only=True,
    skip_missing_text=True,
):
    generator = SuggestionGenerator(training_texts)
    generator.load_data(analysis_storage)

    for batch in chunks(items, 100):
        batch = list(batch)  # need to iterate multiple times

        to_create = []
        to_delete = []
        if missing_only:
            existing_refs = set(
                version.word_suggestion_data.filter(
                    localized_reference__in=[i.localized_reference for i in batch]
                ).values_list("localized_reference", flat=True)
            )
        else:
            existing_refs = None

        if not skip_missing_text:
            if isinstance(batch[0], Verse):
                ensure_text(batch)
        for item in batch:
            generate_suggestions_single_item(
                version,
                item,
                generator,
                localized_reference=localized_reference,
                missing_only=missing_only,
                existing_refs=existing_refs,
                skip_missing_text=skip_missing_text,
                to_create=to_create,
                to_delete=to_delete,
            )
        with transaction.atomic():
            if to_delete:
                logger.info("Deleting %s old items", len(to_delete))
                version.word_suggestion_data.filter(localized_reference__in=to_delete).delete()
            if to_create:
                logger.info("Creating %s items", len(to_create))
                WordSuggestionData.objects.bulk_create(to_create)
        gc.collect()


def generate_suggestions_single_item(
    version,
    item,
    generator,
    localized_reference=None,
    missing_only=True,
    skip_missing_text=True,
    existing_refs=None,
    to_create=None,
    to_delete=None,
):
    if localized_reference is not None and item.localized_reference != localized_reference:
        return

    if skip_missing_text and isinstance(item, Verse) and item.text_saved == "":
        logger.info("Skipping %s %s which has no saved text", version.slug, item.localized_reference)
        return

    text = item.suggestion_text

    if missing_only:
        if item.localized_reference in existing_refs:
            # Don't recreate
            logger.info("Skipping %s %s as suggestions already exist", version.slug, item.localized_reference)
            return
    else:
        # Clear out old suggestions first
        to_delete.append(item.localized_reference)
    logger.info("Generating suggestions for %s %s", version.slug, item.localized_reference)

    item_suggestions = generator.suggestions_for_text(text)
    to_create.append(
        WordSuggestionData(
            version_slug=version.slug,
            language_code=version.language_code,
            localized_reference=item.localized_reference,
            suggestions=item_suggestions,
            hash=hash_text(text),
        )
    )


def items_all_done(version, items, localized_reference=None, missing_only=True):
    if missing_only:
        localized_references = [item.localized_reference for item in items]
        if localized_reference is not None and localized_reference not in localized_references:
            return True
        if version.word_suggestion_data.filter(localized_reference__in=localized_references).count() == len(
            localized_references
        ):
            # All done
            logger.info("Skipping %s %s\n", version.slug, " ".join(localized_references))
            return True
    return False


def hash_text(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def get_whole_book(localized_book_name: str, version, ensure_text_present=True) -> ComboVerse:
    retval = ComboVerse(
        localized_book_name,
        list(
            version.verse_set.filter(
                book_number=get_bible_book_number(version.language_code, localized_book_name), missing=False
            )
        ),
    )
    if ensure_text_present:
        ensure_text(retval.verses)
    return retval


def create_prompt_list(text: str, suggestion_list: list[set[str]]) -> list[list[str]]:
    """
    Given the text of a verse, and a set of suggestions for each word,
    create a "prompt" list, which contains both the suggestions and the correct word.
    """
    # This could be done client side, but it is easy to get sorting correct here.

    if not suggestion_list:
        # We want to indicate that word suggestions are not available, rather than return
        # a suggestion list with only one word (which would be the correct answer),
        # so return empty list:
        return []

    correct_words = split_into_words_for_suggestions(text)
    return [
        sorted(list(suggestions) + [correct_word], key=COLLATER.sort_key)
        for correct_word, suggestions in zip(correct_words, suggestion_list)
    ]
