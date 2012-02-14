from __future__ import absolute_import

from django.test import TestCase

from bibleverses.models import InvalidVerseReference, parse_ref, Verse, BibleVersion


class ParseRefTests(TestCase):

    fixtures = ['test_bible_verses.json']

    def test_no_chapter(self):
        version = BibleVersion.objects.get(slug='KJV')
        self.assertRaises(InvalidVerseReference, lambda: parse_ref('Genesis', version))

    def test_bad_chapter(self):
        version = BibleVersion.objects.get(slug='KJV')
        self.assertRaises(InvalidVerseReference, lambda: parse_ref('Genesis x', version))

    def test_bad_book(self):
        version = BibleVersion.objects.get(slug='KJV')
        self.assertRaises(InvalidVerseReference, lambda: parse_ref('Gospel of Barnabas', version))

    def test_chapter(self):
        version = BibleVersion.objects.get(slug='KJV')
        self.assertEqual(list(version.verse_set.filter(reference__startswith='Genesis 1:')),
                         parse_ref("Genesis 1", version))

    def test_chapter_verse(self):
        version = BibleVersion.objects.get(slug='KJV')
        self.assertEqual([Verse.objects.get(reference="Genesis 1:2", version=version)],
                         parse_ref("Genesis 1:2", version))


    def test_verse_range(self):
        version = BibleVersion.objects.get(slug='KJV')
        self.assertEqual(
            [
                version.verse_set.get(reference="Genesis 1:2"),
                version.verse_set.get(reference="Genesis 1:3"),
                version.verse_set.get(reference="Genesis 1:4"),
                ],
            parse_ref("Genesis 1:2-4", version))

    def test_empty(self):
        version = BibleVersion.objects.get(slug='KJV')
        self.assertRaises(InvalidVerseReference, lambda: parse_ref('Genesis 300:1', version))

    def test_reference_bulk(self):
        version = BibleVersion.objects.get(slug='KJV')
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

