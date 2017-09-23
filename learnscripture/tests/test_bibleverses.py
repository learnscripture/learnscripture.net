# -*- coding:utf-8 -*-
import unittest2

from accounts.models import Identity
from bibleverses.books import get_bible_books
from bibleverses.languages import LANGUAGE_CODE_EN, LANGUAGE_CODE_TR, LANGUAGES
from bibleverses.models import (InvalidVerseReference, TextVersion, Verse, VerseSet, VerseSetType, get_passage_sections,
                                parse_as_bible_localized_reference, split_into_words)
from bibleverses.suggestions.modelapi import create_word_suggestion_data, item_suggestions_need_updating

from .base import AccountTestMixin, TestBase, create_account


class RequireExampleVerseSetsMixin(object):
    SETS = [
        (VerseSetType.SELECTION,
         "Bible 101",
         "bible-101",
         "Some famous verses that everyone ought to know, to get you started.",
         ["John 3:16", "John 14:6"]),
        (VerseSetType.SELECTION,
         "Temptation",
         "temptation",
         "Some help in dealing with common temptations.",
         []),
        (VerseSetType.SELECTION,
         "Basic Gospel",
         "basic-gospel",
         "Great gospel texts",
         ["John 3:16", "Ephesians 2:8"]),
        (VerseSetType.PASSAGE,
         "Psalm 23",
         "psalm-23",
         "",
         ["Psalm 23:1", "Psalm 23:2", "Psalm 23:3", "Psalm 23:4", "Psalm 23:5", "Psalm 23:6"])
    ]

    def setUp(self):
        super(RequireExampleVerseSetsMixin, self).setUp()

        _, account = create_account(username='creatoraccount☺', is_active=False)
        for set_type, name, slug, description, verse_choices in self.SETS:
            vs = VerseSet.objects.create(
                set_type=set_type,
                name=name,
                slug=slug,
                description=description,
                public=True,
                created_by=account)
            for i, ref in enumerate(verse_choices):
                set_order = i + 1
                vs.verse_choices.create(
                    set_order=set_order,
                    localized_reference=ref
                )


class VerseTests(TestBase):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def test_last_verse(self):
        v = Verse.objects.get(localized_reference='Psalm 23:6', version__slug='KJV')
        self.assertTrue(v.is_last_verse_in_chapter())

        v2 = Verse.objects.get(localized_reference='Psalm 23:5', version__slug='KJV')
        self.assertFalse(v2.is_last_verse_in_chapter())

    def test_mark_missing(self):
        version = TextVersion.objects.get(slug='NET')
        # Sanity check:
        self.assertEqual(
            version.verse_set.get(localized_reference="John 3:16").missing,
            False)

        i = Identity.objects.create()
        i.create_verse_status("John 3:16", None, version)
        self.assertEqual(
            i.verse_statuses.filter(localized_reference="John 3:16",
                                    version=version).count(),
            1)

        # Now remove the verse
        Verse.objects.get(localized_reference='John 3:16', version=version).mark_missing()

        # Should have change the Verse object
        self.assertEqual(
            version.verse_set.get(localized_reference="John 3:16").missing,
            True)
        # ...and all UserVerseStatus objects
        self.assertEqual(
            i.verse_statuses.filter(localized_reference="John 3:16",
                                    version=version).count(),
            0)


class VersionTests(TestBase):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def setUp(self):
        super(VersionTests, self).setUp()
        # WSD doesn't get torn down correctly, so do setup each time.
        version = TextVersion.objects.get(slug='KJV')
        version.word_suggestion_data.delete()

        def t(ref):
            return version.verse_set.get(localized_reference=ref).suggestion_text
        create_word_suggestion_data(version=version,
                                    localized_reference='Genesis 1:1',
                                    text=t('Genesis 1:1'),
                                    suggestions=self._gen_1_1_suggestions())
        create_word_suggestion_data(version=version,
                                    localized_reference='Genesis 1:2',
                                    text=t('Genesis 1:2'),
                                    suggestions=self._gen_1_2_suggestions())
        create_word_suggestion_data(version=version,
                                    localized_reference='Genesis 1:3',
                                    text=t('Genesis 1:3'),
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
        self.assertEqual(list(version.verse_set.filter(localized_reference__startswith='Genesis 1:')),
                         version.get_verse_list("Genesis 1"))

    def test_chapter_verse(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertEqual([Verse.objects.get(localized_reference="Genesis 1:2", version=version)],
                         version.get_verse_list("Genesis 1:2"))

    def test_verse_range(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertEqual(
            [
                version.verse_set.get(localized_reference="Genesis 1:2"),
                version.verse_set.get(localized_reference="Genesis 1:3"),
                version.verse_set.get(localized_reference="Genesis 1:4"),
            ],
            version.get_verse_list("Genesis 1:2-4"))

    def test_empty(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertRaises(InvalidVerseReference, lambda: version.get_verse_list('Genesis 300:1'))

    def test_get_verses_by_localized_reference_bulk(self):
        version = TextVersion.objects.get(slug='KJV')
        with self.assertNumQueries(1):
            # Only need one query if all are single verses.
            l1 = version.get_verses_by_localized_reference_bulk(['Genesis 1:1', 'Genesis 1:2', 'Genesis 1:3'])

        with self.assertNumQueries(3):
            # 1 query for single verses,
            # 2 for each combo
            l2 = version.get_verses_by_localized_reference_bulk(['Genesis 1:1', 'Genesis 1:2-3'])

        self.assertEqual(l1['Genesis 1:1'].text, "In the beginning God created the heaven and the earth. ")

        self.assertEqual(l2['Genesis 1:2-3'].text, l1['Genesis 1:2'].text + ' ' + l1['Genesis 1:3'].text)

        self.assertEqual(l2['Genesis 1:2-3'].chapter_number, l1['Genesis 1:2'].chapter_number)

    def test_turkish_get_verse_list(self):
        version = TextVersion.objects.get(slug='TCL02')

        # Single verse
        v_1 = version.get_verse_list('Yuhanna 3:16')[0]
        self.assertTrue(v_1.text.startswith("“Çünkü"))

        # Group of verses
        vl_1 = version.get_verse_list('Mezmur 23:1-3')
        self.assertEqual(len(vl_1), 3)

        # Chapter
        vl_2 = version.get_verse_list('Mezmur 23')
        self.assertEqual(len(vl_2), 6)

    def test_parse_as_bible_localized_reference(self):
        for lang in LANGUAGES:
            for book in get_bible_books(lang.code):
                r = parse_as_bible_localized_reference(lang.code, book,
                                                       allow_whole_book=True)
                self.assertEqual(r, book)

    def test_turkish_abbreviations(self):
        tests = [
            ("1. Timoteos 3:16", "1. Timoteos 3:16"),
            ("1 Timoteos 3:16", "1. Timoteos 3:16"),
            ("1Timoteos 3:16", "1. Timoteos 3:16"),
            ("1tim 3.16", "1. Timoteos 3:16"),
        ]
        for ref, output in tests:
            self.assertEqual(parse_as_bible_localized_reference(LANGUAGE_CODE_TR,
                                                                ref),
                             output,
                             "Failure parsing " + ref)
        # TODO
        # Test:
        #  - upper/lower casing
        #  - tolerance of 'i' for 'ı', "o" for "ö" etc.
        #  - turkish abbreviations.
        #  - tolerance of missing "'" from book names

    def _gen_1_1_suggestions(self):
        # in the beginning...
        return [['and', 'but', 'thou'],
                ['his', 'all', 'a'],
                ['land', 'wilderness', 'sight'],
                ['of', 'between', 'so'],
                ['and', 'of', 'hath'],
                ['man', 'he', 'and'],
                ['lord', 'land', 'children'],
                ['to', 'in', 'that'],
                ['they', 'as', 'earth'],
                ['lord', 'god', 'evening']]

    def _gen_1_2_suggestions(self):
        return [['and', 'but', 'thou'],
                ['he', 'they', 'thou'],
                ['lord', 'priest', 'children'],
                ['and', 'opened', 'that'],
                ['filled', 'of', 'the'],
                ['the', 'number', 'blemish'],
                ['gods', 'over', 'one'],
                ['the', 'he', 'they'],
                ['after', 'but', 'on'],
                ['the', 'he', 'they'],
                ['to', 'and', 'over'],
                ['the', 'in', 'not'],
                ['them', 'him', 'it'],
                ['earth', 'tabernacle', 'inwards'],
                ['and', 'to', 'against'],
                ['all', 'his', 'israel'],
                ['earth', 'lord', 'ground'],
                ['that', 'sleep', 'broken'],
                ['he', 'they', 'thou'],
                ['windows', 'lord', 'priest'],
                ['rested', 'and', 'that'],
                ['jealousy', 'wisdom', 'jacob'],
                ['in', 'is', 'came'],
                ['me', 'lace', 'people'],
                ['his', 'them', 'him'],
                ['earth', 'altar', 'head'],
                ['and', 'to', 'against'],
                ['all', 'his', 'israel'],
                ['earth', 'lord', 'ground']]

    def _gen_1_3_suggestions(self):
        return [['and', 'but', 'thou'],
                ['the', 'he', 'they'],
                ['saw', 'spake', 'made'],
                ['unto', 'behold', 'this'],
                ['the', 'us', 'me'],
                ['more', 'shall', 'was'],
                ['no', 'a', 'lights'],
                ['to', 'the', 'over'],
                ['the', 'his', 'for'],
                ['shall', 'is', 'came'],
                ['a', 'no', 'not']]

    # Tests for suggestions are deterministic because the total number of
    # suggestions stored is less than the number of suggestions we would like to
    # present to the user. We therefore always end up using all the suggestions.
    def test_suggestions(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertEqual(version.get_suggestions_by_localized_reference('Genesis 1:1')[1],
                         ['a', 'all', 'his'])

    def test_suggestions_combo(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertEqual(version.get_suggestions_by_localized_reference('Genesis 1:1-2')[10],
                         ['and', 'but', 'thou'])

    def test_suggestions_bulk(self):
        version = TextVersion.objects.get(slug='KJV')
        with self.assertNumQueries(2, using='default'):
            with self.assertNumQueries(2, using='wordsuggestions'):
                # 4 queries
                # - 1 for WordSuggestionData for v1, v2, v3
                # - 2 for parseref for v2-3,
                # - 1 for WordSuggestionData for v2-3
                d = version.get_suggestions_by_localized_reference_bulk([
                    'Genesis 1:1',
                    'Genesis 1:2',
                    'Genesis 1:3',
                    'Genesis 1:2-3'])
                self.assertEqual(len(d), 4)

    def test_item_suggestions_needs_updating(self):
        v = Verse.objects.get(version__slug='KJV',
                              localized_reference='Genesis 1:1')
        # Already has suggestions set up
        self.assertFalse(item_suggestions_need_updating(v))

        # But if we change the text:
        v.text_saved = v.text_saved + " blah blah."
        v.save()
        self.assertTrue(item_suggestions_need_updating(v))

        # No word suggestion set up:
        v2 = Verse.objects.get(version__slug='KJV',
                               localized_reference='Psalm 23:1')
        self.assertTrue(item_suggestions_need_updating(v2))


class MockUVS(object):
    def __init__(self, localized_reference):
        self.localized_reference = localized_reference


class GetPassageSectionsTests(unittest2.TestCase):

    def test_empty(self):
        uvs_list = [MockUVS('Genesis 1:1'),
                    MockUVS('Genesis 1:2')]
        sections = get_passage_sections(LANGUAGE_CODE_EN, uvs_list, '')
        self.assertEqual([[uvs.localized_reference for uvs in section]
                          for section in sections],
                         [["Genesis 1:1", "Genesis 1:2"]])

    def test_simple_verse_list(self):
        uvs_list = [MockUVS('Genesis 1:1'),
                    MockUVS('Genesis 1:2'),
                    MockUVS('Genesis 1:3'),
                    MockUVS('Genesis 1:4'),
                    MockUVS('Genesis 1:5')]

        sections = get_passage_sections(LANGUAGE_CODE_EN, uvs_list, '1,4')
        self.assertEqual([[uvs.localized_reference for uvs in section]
                          for section in sections],
                         [["Genesis 1:1", "Genesis 1:2", "Genesis 1:3"],
                          ["Genesis 1:4", "Genesis 1:5"]])

    def test_simple_verse_list_missing_first(self):
        uvs_list = [MockUVS('Genesis 1:1'),
                    MockUVS('Genesis 1:2'),
                    MockUVS('Genesis 1:3'),
                    MockUVS('Genesis 1:4'),
                    MockUVS('Genesis 1:5')]

        sections = get_passage_sections(LANGUAGE_CODE_EN, uvs_list, '4')
        self.assertEqual([[uvs.localized_reference for uvs in section]
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

        sections = get_passage_sections(LANGUAGE_CODE_EN, uvs_list, '1:13,2:2,4')
        self.assertEqual([[uvs.localized_reference for uvs in section]
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

        sections = get_passage_sections(LANGUAGE_CODE_EN, uvs_list, '3')
        self.assertEqual([[uvs.localized_reference for uvs in section]
                          for section in sections],
                         [["Genesis 1:1", "Genesis 1:2"],
                          ["Genesis 1:3-4", "Genesis 1:5"]])


class UserVerseStatusTests(RequireExampleVerseSetsMixin, AccountTestMixin, TestBase):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def test_passage_and_section_localized_reference(self):
        # Setup to create UVSs
        identity, account = self.create_account()
        vs = VerseSet.objects.get(name="Psalm 23")
        vs.breaks = "23:4"
        vs.save()
        identity.add_verse_set(vs)

        uvs = identity.verse_statuses.get(localized_reference='Psalm 23:2')

        self.assertEqual(uvs.passage_localized_reference, 'Psalm 23:1-6')
        self.assertEqual(uvs.section_localized_reference, 'Psalm 23:1-3')


class VerseUtilsTests(unittest2.TestCase):

    def test_split_into_words(self):
        self.assertEqual(split_into_words("""and live forever--"'"""),
                         ["and", "live", "forever--\"'"])

        self.assertEqual(split_into_words("two great lights--the greater light"),
                         ["two", "great", "lights--", "the", "greater", "light"])

        self.assertEqual(split_into_words("--some text here"),
                         ["--some", "text", "here"])

    def test_split_into_words_newlines(self):
        text = 'and\r\n"A stone of stumbling,\r\nand a rock of offense.'
        self.assertEqual(split_into_words(text),
                         ['and\n', '"A', 'stone', 'of', 'stumbling,\n', 'and', 'a', 'rock', 'of', 'offense.'])


class SetupEsvMixin(object):
    def setUp(self):
        super(SetupEsvMixin, self).setUp()
        self.esv = self.make_esv()

    def make_esv(self):
        # ESV needs to be created with text empty, but verses existing
        esv = TextVersion.objects.get_or_create(short_name='ESV', slug='ESV')[0]
        esv.verse_set.create(localized_reference='John 3:16',
                             book_number=42,
                             chapter_number=3,
                             verse_number=16,
                             bible_verse_number=26136)
        esv.verse_set.create(localized_reference='John 3:17',
                             book_number=42,
                             chapter_number=3,
                             verse_number=17,
                             bible_verse_number=26137)
        esv.verse_set.create(localized_reference='John 5:4',
                             book_number=42,
                             chapter_number=5,
                             verse_number=4,
                             bible_verse_number=26214)
        return esv


class ESVTests(SetupEsvMixin, TestBase):
    """
    Tests to ensure we can transparently get the ESV text
    """
    # Specifically we are testing a lot of the functionality of 'ensure_text'

    JOHN_316_TEXT = '"For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.'
    JOHN_317_TEXT = 'For God did not send his Son into the world to condemn the world, but in order that the world might be saved through him.'

    def test_get_verse_list(self):
        l = self.esv.get_verse_list('John 3:16')
        text = self.JOHN_316_TEXT
        self.assertEqual(l[0].text, text)
        self._assert_john316_correct()

    def test_combo_verses(self):
        d = self.esv.get_verses_by_localized_reference_bulk(['John 5:4', 'John 3:16-17'])
        self.assertEqual(d['John 5:4'].text, "")
        self.assertEqual(d['John 3:16-17'].text, self.JOHN_316_TEXT + " " + self.JOHN_317_TEXT)

    def test_get_verse_list_missing(self):
        l = self.esv.get_verse_list('John 5:4')
        self.assertEqual(l[0].text, '')

        # 'missing' should be set in the DB
        verse = self.esv.verse_set.get(localized_reference='John 5:4')
        self.assertEqual(verse.text_saved, "")
        self.assertEqual(verse.missing, True)

    def _assert_john316_correct(self):
        self._assert_text_present_and_correct('John 3:16', self.JOHN_316_TEXT)

    def _assert_john317_correct(self):
        self._assert_text_present_and_correct('John 3:17', self.JOHN_316_TEXT)

    def _assert_text_present_and_correct(self, ref, text):
        verse = self.esv.verse_set.get(localized_reference=ref)
        self.assertEqual(verse.text_saved, text)
        self.assertEqual(verse.missing, False)
