# -*- coding: utf8 -*-
"""
Word suggestion API for Django model layer code
"""
import gc
import hashlib
import logging

from django.db import transaction

from bibleverses.constants import BIBLE_BOOKS
from bibleverses.models import TextType, TextVersion, Verse, WordSuggestionData, ensure_text, get_whole_book
from bibleverses.services import partial_data_available
from learnscripture.utils.iterators import chunks

from .exceptions import AnalysisMissing
from .generators import SuggestionGenerator
from .storage import AnalysisStorage
from .trainingtexts import BibleTrainingTexts, CatechismTrainingTexts

logger = logging.getLogger(__name__)


# Normally generate_suggestions is called only by management command, for
# generating in bulk. However, at other times it has been necessary to edit a
# text via the admin, and this triggers 'fix_item' being called to fix up the
# word suggestions.

# See __init__.py for comments about how this code is structured.


def fix_item(version_slug, reference, text_saved):
    version = TextVersion.objects.get(slug=version_slug)
    item = version.get_item_by_reference(reference)
    if getattr(item, 'missing', False):
        return  # Doesn't need fixing

    # 'text_saved' is passed through, to ensure that this process (Celery) sees
    # the same value that was being saved in the Django process. We can also
    # avoid generating a warning in ensure_text this way.
    if text_saved is not None:
        item.text_saved = text_saved

    # Before recreating, check if the hash has changed. This is especially
    # important for versions where we only partially store locally and have to
    # fetch the data again (triggering a save and this function being called)
    if not item_suggestions_need_updating(item):
        logger.info("Skipping creation of word suggestions for unchanged %s %s",
                    version_slug, reference)
        return

    # To avoid loading large amounts of data over the API,
    # we make it illegal to load any.
    # We are going to have problems fixing the word suggestions, because the
    # current algo assumes access to the whole text. So just log a warning
    disallow_loading = partial_data_available(version_slug)
    try:
        generate_suggestions(version, missing_only=False, ref=reference, disallow_loading=disallow_loading,
                             text_saved=text_saved)
    except AnalysisMissing as e:
        logger.warn("%r", e.args[0])
        logger.warn("Need to create word suggestions for %s %s but can't because text is not available and saved analysis is not complete",
                    version_slug, reference)
        return


def item_suggestions_need_updating(item):
    version_slug = item.text_version.slug
    reference = item.reference
    suggestion_data = WordSuggestionData.objects.filter(version_slug=version_slug,
                                                        reference=reference).first()

    if suggestion_data is None:
        return True
    else:
        saved_hash = suggestion_data.hash
        current_hash = hash_text(item.suggestion_text)
        return saved_hash != current_hash


def generate_suggestions(version, ref=None, missing_only=True,
                         disallow_loading=False,
                         text_saved=None):
    analysis_storage = AnalysisStorage()
    if version.text_type == TextType.BIBLE:
        if ref is not None:
            v = version.get_verse_list(ref)[0]
            if text_saved is not None:
                v.text_saved = text_saved
            book = BIBLE_BOOKS[v.book_number]
            items = [v]
            training_texts = BibleTrainingTexts(text=version, books=[book],
                                                disallow_loading=disallow_loading)
            logger.info("Generating for %s", ref)
            generate_suggestions_for_items(
                analysis_storage,
                version, items,
                training_texts, ref=ref, missing_only=missing_only)
        else:
            for book in BIBLE_BOOKS:
                generate_suggestions_for_book(analysis_storage, version, book, missing_only=missing_only)

    elif version.text_type == TextType.CATECHISM:
        training_texts = CatechismTrainingTexts(text=version, disallow_loading=disallow_loading)
        items = list(version.qapairs.all())
        if items_all_done(version, items, ref=ref, missing_only=missing_only):
            return

        generate_suggestions_for_items(
            analysis_storage,
            version, items, training_texts,
            ref=ref, missing_only=missing_only)


def generate_suggestions_for_book(analysis_storage, version, book, missing_only=True):
    logger.info("Generating for %s", book)
    items = get_whole_book(book, version, ensure_text_present=False).verses
    if items_all_done(version, items, missing_only=missing_only):
        return
    training_texts = BibleTrainingTexts(text=version, books=[book])
    generate_suggestions_for_items(
        analysis_storage,
        version, items,
        training_texts, missing_only=missing_only)


def generate_suggestions_for_items(analysis_storage, version, items, training_texts, ref=None,
                                   missing_only=True, skip_missing_text=True):
    generator = SuggestionGenerator(training_texts)
    generator.load_data(analysis_storage)

    for batch in chunks(items, 100):
        batch = list(batch)  # need to iterate multiple times

        to_create = []
        to_delete = []
        if missing_only:
            existing_refs = set(
                version.word_suggestion_data
                .filter(reference__in=[i.reference for i in batch])
                .values_list('reference', flat=True))
        else:
            existing_refs = None

        if not skip_missing_text:
            if isinstance(batch[0], Verse):
                ensure_text(batch)
        for item in batch:
            generate_suggestions_single_item(version, item,
                                             generator,
                                             ref=ref, missing_only=missing_only,
                                             existing_refs=existing_refs,
                                             skip_missing_text=skip_missing_text,
                                             to_create=to_create,
                                             to_delete=to_delete)
        with transaction.atomic():
            if to_delete:
                logger.info("Deleting %s old items", len(to_delete))
                version.word_suggestion_data.filter(reference__in=to_delete).delete()
            if to_create:
                logger.info("Creating %s items", len(to_create))
                WordSuggestionData.objects.bulk_create(to_create)
        gc.collect()


def generate_suggestions_single_item(version, item,
                                     generator,
                                     ref=None,
                                     missing_only=True,
                                     skip_missing_text=True,
                                     existing_refs=None,
                                     to_create=None,
                                     to_delete=None):
    if ref is not None and item.reference != ref:
        return

    if (skip_missing_text and isinstance(item, Verse) and
            item.text_saved == ""):
        logger.info("Skipping %s %s which has no saved text", version.slug, item.reference)
        return

    text = item.suggestion_text

    if missing_only:
        if item.reference in existing_refs:
            # Don't recreate
            logger.info("Skipping %s %s as suggestions already exist", version.slug, item.reference)
            return
    else:
        # Clear out old suggestions first
        to_delete.append(item.reference)
    logger.info("Generating suggestions for %s %s", version.slug, item.reference)

    item_suggestions = generator.suggestions_for_text(text)
    to_create.append(WordSuggestionData(version_slug=version.slug,
                                        reference=item.reference,
                                        suggestions=item_suggestions,
                                        hash=hash_text(text),
                                        ))


def items_all_done(version, items, ref=None, missing_only=True):
    if missing_only:
        references = [item.reference for item in items]
        if ref is not None and ref not in references:
            return True
        if version.word_suggestion_data.filter(reference__in=references).count() == len(references):
            # All done
            logger.info("Skipping %s %s\n", version.slug, ' '.join(references))
            return True
    return False


def hash_text(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()
