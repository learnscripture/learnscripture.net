"""
Services for retrieving Bible and text data, where necessary.
"""
# All code specific to certain versions is in this module,
# rather than in bibleverses.models

import logging
import re
import time
import urllib.parse

import requests
from django.db import models
from pyquery import PyQuery

from learnscripture.utils.iterators import chunks

logger = logging.getLogger(__name__)


# ----- ESV v2 API service -----

ESV_V2_BASE_URL = "http://www.esvapi.org/v2/rest/"

# For batch size, found in practice that above 140 with long references (e.g. "1
# Chronicles"), we can get 'Connection reset' errors, probably related to the
# excessively long query string that is generated. We play safe here:
ESV_V2_BATCH_SIZE = 80


def do_esv_v2_api(method, params):
    url = ESV_V2_BASE_URL + method + "?" + "&".join(params)
    logger.info("ESV v2 query %s", url)
    return requests.get(url).content.decode("utf-8")


def get_esv_v2(localized_reference_list, batch_size=ESV_V2_BATCH_SIZE):
    from django.conf import settings

    first_time = True
    sections = {}
    for batch in chunks(localized_reference_list, batch_size):
        if not first_time:
            time.sleep(1)  # Don't hammer the API.

        params = [
            f"key={settings.ESV_V2_API_KEY}",
            f"passage={urllib.parse.quote(';'.join(batch))}",
            "include-short-copyright=0",
            # Starting with plain text is easier than messing around
            # with massaging HTML, even if it means we have to parse
            # the output in a slightly adhoc way.
            "output-format=plain-text",
            "include-passage-horizontal-lines=0",
            "include-heading-horizontal-lines=0",
            "include-footnotes=0",
            "include-subheadings=0",
            "include-headings=0",
            "line-length=0",
        ]

        text = do_esv_v2_api("passageQuery", params)
        first_time = False

        # Split into passages
        current_section = None
        for line in text.split("\n"):
            l2 = line.strip()
            if l2 == "":
                continue
            if line[0] != " " and l2 in localized_reference_list:
                current_section = l2
            else:
                if current_section is None:
                    # This can happen when ESV sends us back things we didn't
                    # ask for e.g. asking for John 5:4 it sends us John 5:3-5
                    pass
                else:
                    l2 = re.sub(r"\[[\d:]*\]", "", l2).strip()
                    prev = sections[current_section] + "\n" if current_section in sections else ""
                    sections[current_section] = prev + l2

    fix_esv_v2_bugs(sections, localized_reference_list)

    return sorted(sections.items())


# The ESV API incorrectly returns nothing for these items
# (seems to only apply with output-format=plain-text)
MISSING_ESV_V2 = {
    "John 8:1": "but Jesus went to the Mount of Olives.",
}


def fix_esv_v2_bugs(items, needed_localized_references):
    for ref in MISSING_ESV_V2.keys():
        if ref in needed_localized_references:
            items[ref] = MISSING_ESV_V2[ref]


def search_esv_v2(version, words, page, page_size):
    from django.conf import settings

    from bibleverses.models import VerseSearchResult

    params = [
        f"key={settings.ESV_V2_API_KEY}",
        f"words={words}",
        "include-short-copyright=0",
        "include-passage-horizontal-lines=0",
        "include-heading-horizontal-lines=0",
        "include-footnotes=0",
        "include-subheadings=0",
        "include-headings=0",
        "page=%d" % (page + 1),
        "results-per-page=%d" % page_size,
    ]

    result_text = do_esv_v2_api("query", params)
    # Split into results
    pq = PyQuery(result_text)
    results = []
    for elem in pq.find("p.search-result"):
        pq2 = PyQuery(elem)
        ref = pq2.find(".search-result-head a")[0].text_content()
        for item in elem.getchildren():
            if item.tag == "span" and item.attrib.get("class", "") in [
                "search-result-head",
                "search-result-text-heading",
            ]:
                item.drop_tree()
        text = elem.text_content()
        results.append((ref, text))

    verses = version.get_verses_by_localized_reference_bulk([r for r, t in results], fetch_text=False)
    verse_list = []
    for ref, text in results:
        verse = verses[ref]
        verse.text_saved = text
        verse_list.append(highlight_search_words(verse, words))

    # We don't strictly have enough information to work out if there are more
    # results or not, if there is an exact multiple of $page_size results.
    # We assume there are more pages in this case, we can always discover
    # later that there are not.
    more_results = len(verse_list) >= page_size
    return [VerseSearchResult(v.localized_reference, [v]) for v in verse_list], more_results


ESV_MAX_STORED_CONSECUTIVE_VERSES = 500


def adjust_stored_esv(version_slug):
    # V2 API: See terms of usage at http://www.esvapi.org/
    from bibleverses.books import get_bible_books
    from bibleverses.models import TextVersion

    esv = TextVersion.objects.get(slug=version_slug)
    for book_num, book_name in enumerate(get_bible_books(esv.language_code)):
        book_verses = esv.verse_set.filter(book_number=book_num, missing=False)
        # Work out what half a book is.
        d = book_verses.aggregate(start=models.Min("bible_verse_number"), end=models.Max("bible_verse_number"))
        book_size = d["end"] - d["start"] + 1
        max_allowed = min(ESV_MAX_STORED_CONSECUTIVE_VERSES, book_size // 2)
        found = book_verses.filter(text_fetched_at__isnull=False)
        found_count = found.count()
        if found_count > max_allowed:
            to_blank = found_count - max_allowed
            # For now, do a simple FIFO, rather than attempting to evict
            # according to popularity.
            to_blank_ids = found.order_by("text_fetched_at")[:to_blank].values_list("id", flat=True)
            logger.info("Blanking %s verses from ESV %s", len(to_blank_ids), book_name)
            found.filter(id__in=to_blank_ids).update(text_saved="", text_fetched_at=None)


# ----- All services -----


def highlight_search_words(verse, words):
    text = verse.text
    for word in words.split(" "):
        if len(word) < 2:
            # Easily get memory exhaustion if we don't skip '', and in general
            # looks bad for short words of length 1 (because our highlighting
            # scheme is very simplistic)
            continue
        text = text.replace(word, f"**{word}**")
    verse.text_saved = text
    return verse


_FETCH_SERVICES = {
    # Temporarily disable
    # 'ESV': get_esv_v2,
}

_SEARCH_SERVICES = {
    # 'ESV': search_esv_v2,
}

# Versions where we are only allowed to store partial data locally:
_PARTIAL_DATA_VERSIONS = {
    # 'ESV'
}


def get_fetch_service(version_slug):
    return _FETCH_SERVICES.get(version_slug, None)


def get_search_service(version_slug):
    return _SEARCH_SERVICES.get(version_slug, None)


def partial_data_available(version_slug):
    return version_slug in _PARTIAL_DATA_VERSIONS
