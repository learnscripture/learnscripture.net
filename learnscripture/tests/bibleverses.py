from __future__ import absolute_import

from django.utils import unittest
from django.test import TestCase

from accounts.models import Identity
from bibleverses.models import InvalidVerseReference, Verse, TextVersion, get_passage_sections, VerseSet, VerseChoice, UserVerseStatus
from .base import AccountTestMixin


class VerseTests(TestCase):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def test_last_verse(self):
        v = Verse.objects.get(reference='Psalm 23:6', version__slug='KJV')
        self.assertTrue(v.is_last_verse_in_chapter())

        v2 = Verse.objects.get(reference='Psalm 23:5', version__slug='KJV')
        self.assertFalse(v2.is_last_verse_in_chapter())

    def test_mark_missing(self):
        version = TextVersion.objects.get(slug='NET')
        # Sanity check:
        self.assertEqual(
            version.verse_set.get(reference="John 3:16").missing,
            False)

        i = Identity.objects.create()
        i.create_verse_status("John 3:16", None, version)
        self.assertEqual(
            i.verse_statuses.filter(reference="John 3:16",
                                    version=version).count(),
            1)

        # Now remove the verse
        Verse.objects.get(reference='John 3:16', version=version).mark_missing()

        # Should have change the Verse object
        self.assertEqual(
            version.verse_set.get(reference="John 3:16").missing,
            True)
        # ...and all UserVerseStatus objects
        self.assertEqual(
            i.verse_statuses.filter(reference="John 3:16",
                                    version=version).count(),
            0)

class ParseRefTests(TestCase):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def test_no_chapter(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertRaises(InvalidVerseReference, lambda: version.get_verse_list('Genesis'))

    def test_bad_chapter(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertRaises(InvalidVerseReference, lambda: version.get_verse_list('Genesis x'))

    def test_bad_book(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertRaises(InvalidVerseReference, lambda: version.get_verse_list('Gospel of Barnabas'))

    def test_chapter(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertEqual(list(version.verse_set.filter(reference__startswith='Genesis 1:')),
                         version.get_verse_list("Genesis 1"))

    def test_chapter_verse(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertEqual([Verse.objects.get(reference="Genesis 1:2", version=version)],
                         version.get_verse_list("Genesis 1:2"))


    def test_verse_range(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertEqual(
            [
                version.verse_set.get(reference="Genesis 1:2"),
                version.verse_set.get(reference="Genesis 1:3"),
                version.verse_set.get(reference="Genesis 1:4"),
                ],
            version.get_verse_list("Genesis 1:2-4"))

    def test_empty(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertRaises(InvalidVerseReference, lambda: version.get_verse_list('Genesis 300:1'))

    def test_reference_bulk(self):
        version = TextVersion.objects.get(slug='KJV')
        with self.assertNumQueries(1):
            # Only need one query if all are single verses.
            l1 = version.get_verses_by_reference_bulk(['Genesis 1:1', 'Genesis 1:2', 'Genesis 1:3'])

        with self.assertNumQueries(3):
            # 1 query for single verses,
            # 2 for each combo
            l2 = version.get_verses_by_reference_bulk(['Genesis 1:1', 'Genesis 1:2-3'])

        self.assertEqual(l1['Genesis 1:1'].text, "In the beginning God created the heaven and the earth. ")

        self.assertEqual(l2['Genesis 1:2-3'].text, l1['Genesis 1:2'].text + ' ' + l1['Genesis 1:3'].text)

        self.assertEqual(l2['Genesis 1:2-3'].chapter_number, l1['Genesis 1:2'].chapter_number)


class MockUVS(object):
    def __init__(self, reference):
        self.reference = reference


class GetPassageSectionsTests(unittest.TestCase):

    def test_empty(self):
        uvs_list = [MockUVS('Genesis 1:1'),
                    MockUVS('Genesis 1:2')]
        sections = get_passage_sections(uvs_list, '')
        self.assertEqual([[uvs.reference for uvs in section]
                          for section in sections],
                         [["Genesis 1:1", "Genesis 1:2"]])


    def test_simple_verse_list(self):
        uvs_list = [MockUVS('Genesis 1:1'),
                    MockUVS('Genesis 1:2'),
                    MockUVS('Genesis 1:3'),
                    MockUVS('Genesis 1:4'),
                    MockUVS('Genesis 1:5')]

        sections = get_passage_sections(uvs_list, '1,4')
        self.assertEqual([[uvs.reference for uvs in section]
                          for section in sections],
                         [["Genesis 1:1", "Genesis 1:2", "Genesis 1:3"],
                          ["Genesis 1:4", "Genesis 1:5"]])

    def test_simple_verse_list_missing_first(self):
        uvs_list = [MockUVS('Genesis 1:1'),
                    MockUVS('Genesis 1:2'),
                    MockUVS('Genesis 1:3'),
                    MockUVS('Genesis 1:4'),
                    MockUVS('Genesis 1:5')]

        sections = get_passage_sections(uvs_list, '4')
        self.assertEqual([[uvs.reference for uvs in section]
                          for section in sections],
                         [["Genesis 1:1", "Genesis 1:2", "Genesis 1:3"],
                          ["Genesis 1:4", "Genesis 1:5"]])

    def test_chapter_and_verse(self):
        uvs_list = [MockUVS('Genesis 1:11'),
                    MockUVS('Genesis 1:12'),
                    MockUVS('Genesis 1:13'),
                    MockUVS('Genesis 2:1'),
                    MockUVS('Genesis 2:2'),
                    MockUVS('Genesis 2:3'),
                    MockUVS('Genesis 2:4'),
                    MockUVS('Genesis 2:5')]

        sections = get_passage_sections(uvs_list, '1:13,2:2,4')
        self.assertEqual([[uvs.reference for uvs in section]
                          for section in sections],
                         [["Genesis 1:11", "Genesis 1:12"],
                          ["Genesis 1:13", "Genesis 2:1"],
                          ["Genesis 2:2", "Genesis 2:3"],
                          ["Genesis 2:4", "Genesis 2:5"],
                          ])

    def test_combo_verses(self):
        uvs_list = [MockUVS('Genesis 1:1'),
                    MockUVS('Genesis 1:2'),
                    MockUVS('Genesis 1:3-4'),
                    MockUVS('Genesis 1:5')]

        sections = get_passage_sections(uvs_list, '3')
        self.assertEqual([[uvs.reference for uvs in section]
                          for section in sections],
                         [["Genesis 1:1", "Genesis 1:2"],
                          ["Genesis 1:3-4", "Genesis 1:5"]])


class UserVerseStatusTests(AccountTestMixin, TestCase):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def test_passage_and_section_reference(self):
        # Setup to create UVSs
        identity, account = self.create_account()
        vs = VerseSet.objects.get(name="Psalm 23")
        vs.breaks = "23:4"
        vs.save()
        identity.add_verse_set(vs)

        uvs = identity.verse_statuses.get(reference='Psalm 23:2')

        self.assertEqual(uvs.passage_reference, 'Psalm 23:1-6')
        self.assertEqual(uvs.section_reference, 'Psalm 23:1-3')


class ESVTests(TestCase):
    """
    Tests to ensure we can transparently get the ESV text
    """

    def make_esv(self):
        # ESV needs to be created with text empty, but verses existing
        esv = TextVersion.objects.get_or_create(short_name='ESV')[0]
        esv.verse_set.create(reference='John 3:16',
                             book_number=42,
                             chapter_number=3,
                             verse_number=16,
                             bible_verse_number=26136)
        return esv

    def test_get_verse_list(self):
        esv = self.make_esv()
        l = esv.get_verse_list('John 3:16')
        text = '"For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.'
        self.assertEqual(l[0].text, text)
        # Now it should be cached in DB
        self.assertEqual(esv.verse_set.get(reference='John 3:16').text, text)
