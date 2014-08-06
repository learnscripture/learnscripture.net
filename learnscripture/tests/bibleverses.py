from __future__ import absolute_import

import unittest2

from django.test import TestCase

from accounts.models import Identity
from bibleverses.models import InvalidVerseReference, Verse, TextVersion, get_passage_sections, VerseSet, split_into_words
from .base import AccountTestMixin


__all__ = ['VerseTests', 'VersionTests', 'GetPassageSectionsTests', 'UserVerseStatusTests', 'ESVTests']

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

class VersionTests(TestCase):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']


    def setUp(self):
        super(VersionTests, self).setUp()
        # WSD doesn't get torn down correctly, so do setup each time.
        version = TextVersion.objects.get(slug='KJV')
        version.word_suggestion_data.delete()
        version.create_word_suggestion_data(reference='Genesis 1:1',
                                            suggestions=self._gen_1_1_suggestions())
        version.create_word_suggestion_data(reference='Genesis 1:2',
                                            suggestions=self._gen_1_2_suggestions())
        version.create_word_suggestion_data(reference='Genesis 1:3',
                                            suggestions=self._gen_1_3_suggestions())

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


    def _gen_1_1_suggestions(self):
        return \
            [[[u'and', 1.0, 0],                        # in
              [u'but', 0.049, 0],
              [u'thou', 0.037, 0]],
             [[u'his', 1.0, 0],                        # the
              [u'all', 0.740, 0],
              [u'a', 0.653, 0]],
             [[u'land', 1.0, 0],                       # beginning
              [u'wilderness', 0.374, 0],
              [u'sight', 0.258, 0]],
             [[u'of', 1.0, 0],                         # God
              [u'between', 0.158, 0],
              [u'so', 0.158, 0]],
             [[u'and', 1.0, 0],                        # created
              [u'of', 0.736, 0],
              [u'hath', 0.684, 0]],
             [[u'man', 1.0, 0],                        # the
              [u'he', 0.516, 0],
              [u'and', 0.45, 0]],
             [[u'lord', 1.0, 0],                       # heavens
              [u'land', 0.289, 0],
              [u'children', 0.289, 0]],
             [[u'to', 1.0, 0],                         # and
              [u'in', 0.541, 0],
              [u'that', 0.416, 0]],
             [[u'they', 1.0, 0],                       # the
              [u'as', 0.967, 0],
              [u'earth', 0.233, 0]],
             [[u'lord', 1.0, 0],                       # earth
              [u'god', 0.404, 0],
              [u'evening', 0.403, 0]]]

    def _gen_1_2_suggestions(self):
        return \
            [[[u'and', 1.0, 0],
              [u'but', 0.049, 0],
              [u'thou', 0.035, 0]],
             [[u'he', 1.0, 0],
              [u'they', 0.593, 0],
              [u'thou', 0.403, 0]],
             [[u'lord', 1.0, 0],
              [u'priest', 0.335, 0],
              [u'children', 0.198, 0]],
             [[u'and', 1.0, 0],
              [u'opened', 0.807, 0],
              [u'that', 0.415, 0]],
             [[u'filled', 1.0, 0],
              [u'of', 0.203, 0],
              [u'the', 0.049, 0]],
             [[u'the', 1.0, 0],
              [u'number', 0.772, 0],
              [u'blemish', 0.191, 0]],
             [[u'gods', 1.0, 0],
              [u'over', 1.0, 0],
              [u'one', 1.0, 0]],
             [[u'the', 1.0, 0],
              [u'he', 0.443, 0],
              [u'they', 0.263, 0]],
             [[u'after', 1.0, 0],
              [u'but', 1.0, 0],
              [u'on', 1.0, 0]],
             [[u'the', 1.0, 0],
              [u'he', 0.088, 0],
              [u'they', 0.052, 0]],
             [[u'to', 1.0, 0],
              [u'and', 0.222, 0],
              [u'over', 0.055, 0]],
             [[u'the', 1.0, 0],
              [u'in', 0.68, 0],
              [u'not', 0.58, 0]],
             [[u'them', 1.0, 0],
              [u'him', 0.991, 0],
              [u'it', 0.979, 0]],
             [[u'earth', 1.0, 0],
              [u'tabernacle', 0.849, 0],
              [u'inwards', 0.845, 0]],
             [[u'and', 1.0, 0],
              [u'to', 0.329, 0],
              [u'against', 0.235, 0]],
             [[u'all', 1.0, 0],
              [u'his', 0.520, 0],
              [u'israel', 0.296, 0]],
             [[u'earth', 1.0, 0],
              [u'lord', 0.306, 0],
              [u'ground', 0.282, 0]],
             [[u'that', 1.0, 0],
              [u'sleep', 0.047, 0],
              [u'broken', 0.023, 0]],
             [[u'he', 1.0, 0],
              [u'they', 0.593, 0],
              [u'thou', 0.403, 0]],
             [[u'windows', 1.0, 0],
              [u'lord', 0.249, 0],
              [u'priest', 0.083, 0]],
             [[u'rested', 1.0, 0],
              [u'and', 0.157, 0],
              [u'that', 0.125, 0]],
             [[u'jealousy', 1.0, 0],
              [u'wisdom', 0.666, 0],
              [u'jacob', 0.333, 0]],
             [[u'in', 1.0, 0],
              [u'is', 0.507, 0],
              [u'came', 0.497, 0]],
             [[u'me', 1.0, 0],
              [u'lace', 0.25, 0],
              [u'people', 0.25, 0]],
             [[u'his', 1.0, 0],
              [u'them', 0.900, 0],
              [u'him', 0.860, 0]],
             [[u'earth', 1.0, 0],
              [u'altar', 0.205, 0],
              [u'head', 0.080, 0]],
             [[u'and', 1.0, 0],
              [u'to', 0.411, 0],
              [u'against', 0.294, 0]],
             [[u'all', 1.0, 0],
              [u'his', 0.520, 0],
              [u'israel', 0.296, 0]],
             [[u'earth', 1.0, 0],
              [u'lord', 0.306, 0],
              [u'ground', 0.282, 0]]]

    def _gen_1_3_suggestions(self):
        return \
            [[[u'and', 1.0, 0],
              [u'but', 0.049, 0],
              [u'thou', 0.035, 0]],
             [[u'the', 1.0, 0],
              [u'he', 0.443, 0],
              [u'they', 0.263, 0]],
             [[u'saw', 1.0, 0],
              [u'spake', 0.631, 0],
              [u'made', 0.508, 0]],
             [[u'unto', 1.0, 0],
              [u'behold', 0.094, 0],
              [u'this', 0.078, 0]],
             [[u'the', 1.0, 0],
              [u'us', 0.430, 0],
              [u'me', 0.185, 0]],
             [[u'more', 1.0, 0],
              [u'shall', 0.248, 0],
              [u'was', 0.243, 0]],
             [[u'no', 1.0, 0],
              [u'a', 0.922, 0],
              [u'lights', 0.807, 0]],
             [[u'to', 1.0, 0],
              [u'the', 0.850, 0],
              [u'over', 0.400, 0]],
             [[u'the', 1.0, 0],
              [u'his', 0.567, 0],
              [u'for', 0.280, 0]],
             [[u'shall', 1.0, 0],
              [u'is', 0.503, 0],
              [u'came', 0.468, 0]],
             [[u'a', 1.0, 0],
              [u'no', 0.787, 0],
              [u'not', 0.502, 0]]]

    def test_suggestions(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertEqual(version.get_suggestion_pairs_by_reference('Genesis 1:1')[1],
                         [('his', 1.0),
                          ('all', 0.740),
                          ('a', 0.653),
                          ])

    def test_suggestions_combo(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertEqual(version.get_suggestion_pairs_by_reference('Genesis 1:1-2')[10],
                         [('and', 1.0),
                          ('but', 0.049),
                          ('thou', 0.035)])

    def test_suggestions_bulk(self):
        version = TextVersion.objects.get(slug='KJV')
        with self.assertNumQueries(2, using='default'):
            with self.assertNumQueries(2, using='wordsuggestions'):
                # 4 queries
                # - 1 for WordSuggestionData for v1, v2, v3
                # - 2 for parseref for v2-3,
                # - 1 for WordSuggestionData for v2-3
                d = version.get_suggestion_pairs_by_reference_bulk(['Genesis 1:1',
                                                                    'Genesis 1:2',
                                                                    'Genesis 1:3',
                                                                    'Genesis 1:2-3'])
                self.assertEqual(len(d), 4)

    def test_suggestions_update(self):
        version = TextVersion.objects.get(slug='KJV')
        version.record_word_mistakes('Genesis 1:1', [[0, 'but'],
                                                     [1, 'his']])
        self.assertEqual(version.get_suggestion_pairs_by_reference('Genesis 1:1')[0],
                         [(u'and', 1.0), (u'but', 1.049), (u'thou', 0.037)])
        self.assertEqual(version.get_suggestion_pairs_by_reference('Genesis 1:1')[1],
                         [(u'his', 2.0), (u'all', 0.740), (u'a', 0.653)])

        version.record_word_mistakes('Genesis 1:2-3', [[1, 'they'],
                                                       [30, 'he']]) # 29 words in Gen 1:2, this is word at index 1 in Gen 1:3
        self.assertEqual(version.get_suggestion_pairs_by_reference('Genesis 1:2')[1],
                         [(u'he', 1.0), (u'they', 1.593), (u'thou', 0.403)])
        self.assertEqual(version.get_suggestion_pairs_by_reference('Genesis 1:3')[1],
                         [(u'the', 1.0), (u'he', 1.443), (u'they', 0.263)])


class MockUVS(object):
    def __init__(self, reference):
        self.reference = reference


class GetPassageSectionsTests(unittest2.TestCase):

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


class VerseUtilsTests(unittest2.TestCase):

    def test_split_into_words(self):
        self.assertEqual(split_into_words("""and live forever--"'"""),
                         ["and", "live", "forever--\"'"])

        self.assertEqual(split_into_words("two great lights--the greater light"),
                         ["two", "great", "lights--", "the", "greater", "light"])

        self.assertEqual(split_into_words("--some text here"),
                         ["--some", "text", "here"])


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
