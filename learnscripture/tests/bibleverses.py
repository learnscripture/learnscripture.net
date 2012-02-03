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
