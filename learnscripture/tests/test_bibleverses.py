# -*- coding:utf-8 -*-
import unittest2
from django_ftl import override

from accounts.models import Identity
from bibleverses.books import get_bible_book_number, get_bible_books, is_single_chapter_book
from bibleverses.languages import LANGUAGE_CODE_EN, LANGUAGE_CODE_TR, LANGUAGES, normalize_reference_input_turkish
from bibleverses.models import (InvalidVerseReference, TextVersion, Verse, VerseSet, VerseSetType, get_passage_sections,
                                is_continuous_set, split_into_words)
from bibleverses.parsing import (ParsedReference, internalize_localized_reference,
                                 parse_unvalidated_localized_reference, parse_validated_localized_reference)
from bibleverses.suggestions.modelapi import create_word_suggestion_data, item_suggestions_need_updating

from .base import AccountTestMixin, BibleVersesMixin, TestBase, get_or_create_any_account


class RequireExampleVerseSetsMixin(BibleVersesMixin):
    SETS = [
        (VerseSetType.SELECTION,
         "Bible 101",
         "bible-101",
         "Some famous verses that everyone ought to know, to get you started.",
         ["John 3:16", "John 14:6", "Ephesians 2:8-9"]),
        (VerseSetType.SELECTION,
         "Temptation",
         "temptation",
         "Some help in dealing with common temptations.",
         []),
        (VerseSetType.SELECTION,
         "Basic Gospel",
         "basic-gospel",
         "Great gospel texts",
         ["John 3:16", "Ephesians 2:8-9"]),
        (VerseSetType.PASSAGE,
         "Psalm 23",
         "psalm-23",
         "",
         ["Psalm 23:1", "Psalm 23:2", "Psalm 23:3", "Psalm 23:4", "Psalm 23:5", "Psalm 23:6"])
    ]

    def setUp(self):
        super().setUp()
        for set_type, name, slug, description, verse_choices in self.SETS:
            self.create_verse_set(set_type, name, slug, description, verse_choices)

    def create_verse_set(self, set_type, name, slug, description, en_ref_list):
        account = get_or_create_any_account(username='creatoraccount☺', is_active=False)
        vs = VerseSet.objects.create(
            language_code='en',
            set_type=set_type,
            name=name,
            slug=slug,
            description=description,
            public=True,
            created_by=account)
        for i, ref in enumerate(en_ref_list):
            set_order = i + 1
            vs.verse_choices.create(
                set_order=set_order,
                internal_reference=internalize_localized_reference(LANGUAGE_CODE_EN, ref)
            )
        return vs


class VerseTests(BibleVersesMixin, TestBase):

    def test_mark_missing(self):
        version = self.NET
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


class VersionTests(BibleVersesMixin, TestBase):
    databases = {'default', 'wordsuggestions'}

    def setUp(self):
        super(VersionTests, self).setUp()
        version = self.KJV

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
        self.assertRaises(InvalidVerseReference, lambda: self.KJV.get_verse_list('Genesis'))

    def test_bad_chapter(self):
        self.assertRaises(InvalidVerseReference, lambda: self.KJV.get_verse_list('Genesis x'))

    def test_bad_book(self):
        self.assertRaises(InvalidVerseReference, lambda: self.KJV.get_verse_list('Gospel of Barnabas'))

    def test_chapter(self):
        self.assertEqual(list(self.KJV.verse_set.filter(localized_reference__startswith='Genesis 1:')),
                         self.KJV.get_verse_list("Genesis 1"))

    def test_chapter_verse(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertEqual([Verse.objects.get(localized_reference="Genesis 1:2", version=version)],
                         version.get_verse_list("Genesis 1:2"))

    def test_verse_range(self):
        version = self.KJV
        self.assertEqual(
            [
                version.verse_set.get(localized_reference="Genesis 1:2"),
                version.verse_set.get(localized_reference="Genesis 1:3"),
                version.verse_set.get(localized_reference="Genesis 1:4"),
            ],
            version.get_verse_list("Genesis 1:2-4"))

    def test_empty(self):
        with override('en'):
            self.assertRaises(InvalidVerseReference, lambda: self.KJV.get_verse_list('Genesis 300:1'))

    def test_get_verses_by_localized_reference_bulk(self):
        version = self.KJV
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
        version = self.TCL02

        # Single verse
        v_1 = version.get_verse_list('Yuhanna 3:16')[0]
        self.assertTrue(v_1.text.startswith("“Çünkü"))

        # Group of verses
        v_2 = version.get_verse_list('Mezmur 23:1-3')
        self.assertEqual(len(v_2), 3)

        # Chapter
        v_3 = version.get_verse_list('Mezmur 23')
        self.assertEqual(len(v_3), 6)

    def test_get_verse_list_merged(self):
        with self.assertNumQueries(2):
            # We could in theory get this in one query as it is a merged verse,
            # but because it looks like a verse range, we end up in the combo
            # verse route. Fixing this would end up increasing query counts
            # in other cases.
            vl = self.TCL02.get_verse_list("Romalılar 3:25-26")
            self.assertEqual(len(vl), 1)
            self.assertEqual(vl[0].localized_reference, "Romalılar 3:25-26")

    def test_get_verse_list_spanning_merged(self):
        # Here our range spans over the merged verses.
        # This relies on the merged verses having a sensible bible_verse_number,
        # just like other bible verses
        with self.assertNumQueries(2):
            vl = self.TCL02.get_verse_list("Romalılar 3:24-27")
            self.assertEqual(len(vl), 3)
            self.assertEqual(vl[0].localized_reference, "Romalılar 3:24")
            self.assertEqual(vl[1].localized_reference, "Romalılar 3:25-26")
            self.assertEqual(vl[2].localized_reference, "Romalılar 3:27")

    def test_get_verse_list_merged_edges(self):
        # Edge cases
        with self.assertNumQueries(2):
            v1 = self.TCL02.get_verse_list("Romalılar 3:24-25")
            self.assertEqual(len(v1), 2)
            self.assertEqual(v1[0].localized_reference, "Romalılar 3:24")
            self.assertEqual(v1[1].localized_reference, "Romalılar 3:25-26")

        with self.assertNumQueries(2):
            v2 = self.TCL02.get_verse_list("Romalılar 3:26-27")
            self.assertEqual(len(v2), 2)
            self.assertEqual(v2[0].localized_reference, "Romalılar 3:25-26")
            self.assertEqual(v2[1].localized_reference, "Romalılar 3:27")

    def test_get_verses_by_localized_reference_bulk_merged(self):
        version = self.TCL02
        with self.assertNumQueries(1):
            # Only need one query if all are single verses or merged verses
            d1 = version.get_verses_by_localized_reference_bulk(
                ['Romalılar 3:24', 'Romalılar 3:25-26', 'Romalılar 3:27'])
            self.assertEqual(d1['Romalılar 3:24'].text,
                             "İnsanlar İsa Mesih'te olan kurtuluşla “Kurtuluşla”, Tanrı'nın lütfuyla, karşılıksız olarak aklanırlar.")
            self.assertEqual(d1['Romalılar 3:25-26'].text,
                             "Tanrı Mesih'i, kanıyla günahları bağışlatan ve imanla benimsenen kurban olarak sundu. Böylece adaletini gösterdi. Çünkü sabredip daha önce işlenmiş günahları cezasız bıraktı. Bunu, adil kalmak ve İsa'ya iman edeni aklamak için şimdiki zamanda kendi adaletini göstermek amacıyla yaptı.")

    def test_get_verses_by_localized_reference_bulk_spanning_merge(self):
        version = self.TCL02
        with self.assertNumQueries(3):
            # 1 for simple ones, 2 for the merged
            d1 = version.get_verses_by_localized_reference_bulk(
                ['Romalılar 3:23', 'Romalılar 3:24-27'])
            self.assertEqual(d1['Romalılar 3:24-27'].text,
                             "İnsanlar İsa Mesih'te olan kurtuluşla “Kurtuluşla”, Tanrı'nın lütfuyla, karşılıksız olarak aklanırlar. Tanrı Mesih'i, kanıyla günahları bağışlatan ve imanla benimsenen kurban olarak sundu. Böylece adaletini gösterdi. Çünkü sabredip daha önce işlenmiş günahları cezasız bıraktı. Bunu, adil kalmak ve İsa'ya iman edeni aklamak için şimdiki zamanda kendi adaletini göstermek amacıyla yaptı. Öyleyse neyle övünebiliriz? Hiçbir şeyle! Hangi ilkeye dayanarak? Yasa'yı yerine getirme ilkesine mi? Hayır, iman ilkesine.")

    def test_get_verses_by_localized_reference_bulk_merged_edges(self):
        version = self.TCL02
        with self.assertNumQueries(3):
            # 1 for simple ones, 2 for the merged
            d1 = version.get_verses_by_localized_reference_bulk(
                ['Romalılar 3:24-25'])
            v = d1['Romalılar 3:24-25']
            self.assertEqual(v.localized_reference, 'Romalılar 3:24-26')
            self.assertEqual(v.text,
                             "İnsanlar İsa Mesih'te olan kurtuluşla “Kurtuluşla”, Tanrı'nın lütfuyla, karşılıksız olarak aklanırlar. Tanrı Mesih'i, kanıyla günahları bağışlatan ve imanla benimsenen kurban olarak sundu. Böylece adaletini gösterdi. Çünkü sabredip daha önce işlenmiş günahları cezasız bıraktı. Bunu, adil kalmak ve İsa'ya iman edeni aklamak için şimdiki zamanda kendi adaletini göstermek amacıyla yaptı.")

        with self.assertNumQueries(1):
            # 1 for simple ones, 2 for the merged
            d1 = version.get_verses_by_localized_reference_bulk(
                ['Romalılar 3:25'])
            v = d1['Romalılar 3:25']
            self.assertEqual(v.localized_reference, 'Romalılar 3:25-26')

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


class ParsingTests(unittest2.TestCase):
    def pv(self, lang, ref):
        """
        parse_validated_localized_reference, with extra checks.
        """
        retval = parse_validated_localized_reference(lang, ref)
        self.assertEqual(retval.canonical_form(), ref)
        return retval

    def pu(self, lang, query, **kwargs):
        """
        parse_unvalidated_localized_reference
        """
        return parse_unvalidated_localized_reference(lang, query, **kwargs)

    def test_unparsable_strict(self):
        self.assertRaises(InvalidVerseReference,
                          lambda: self.pv(LANGUAGE_CODE_EN, "Garbage"))
        self.assertRaises(InvalidVerseReference,
                          lambda: self.pv(LANGUAGE_CODE_EN, "Genesis 1:x"))

    def test_unparsable_loose(self):
        self.assertEqual(self.pu(LANGUAGE_CODE_EN, "Garbage"),
                         None)
        self.assertEqual(self.pu(LANGUAGE_CODE_EN, "Genesis 1:x"),
                         None)

    def test_bad_order_strict(self):
        with override('en'):
            self.assertRaises(InvalidVerseReference,
                              lambda: self.pv(LANGUAGE_CODE_EN, "Genesis 1:3-2"))
            self.assertRaises(InvalidVerseReference,
                              lambda: self.pv(LANGUAGE_CODE_EN, "Genesis 2:1-1:10"))

    def test_bad_order_loose(self):
        with override('en'):
            self.assertRaises(InvalidVerseReference,
                              lambda: self.pu(LANGUAGE_CODE_EN, "genesis 1:3-2"))
            self.assertRaises(InvalidVerseReference,
                              lambda: self.pu(LANGUAGE_CODE_EN, "genesis 2:1 - 1:10"))

    def test_book(self):
        parsed = self.pv(LANGUAGE_CODE_EN,
                         "Genesis 1")
        self.assertEqual(parsed.book_number, 0)
        self.assertEqual(parsed.book_name, "Genesis")
        self.assertEqual(parsed.start_chapter, 1)
        self.assertEqual(parsed.end_chapter, 1)
        self.assertEqual(parsed.start_verse, None)
        self.assertEqual(parsed.end_verse, None)
        self.assertEqual(parsed.is_single_verse(), False)
        self.assertEqual(parsed.is_whole_book(), False)
        self.assertEqual(parsed.is_whole_chapter(), True)

    def test_single_verse_strict(self):
        parsed = self.pv(LANGUAGE_CODE_EN,
                         "Genesis 1:1")
        self._test_single_verse(parsed)

    def test_single_verse_loose(self):
        parsed = self.pu(LANGUAGE_CODE_EN,
                         "Gen 1 v 1")
        self._test_single_verse(parsed)

    def _test_single_verse(self, parsed):
        self.assertEqual(parsed.book_number, 0)
        self.assertEqual(parsed.book_name, "Genesis")
        self.assertEqual(parsed.start_chapter, 1)
        self.assertEqual(parsed.end_chapter, 1)
        self.assertEqual(parsed.start_verse, 1)
        self.assertEqual(parsed.end_verse, 1)
        self.assertEqual(parsed.is_single_verse(), True)
        self.assertEqual(parsed.is_whole_book(), False)
        self.assertEqual(parsed.is_whole_chapter(), False)
        self.assertEqual(parsed.get_start(), parsed)
        self.assertEqual(parsed.get_end(), parsed)

    def test_verse_range_strict(self):
        parsed = self.pv(LANGUAGE_CODE_EN,
                         "Genesis 1:1-2")
        self._test_verse_range(parsed)

    def test_verse_range_loose(self):
        parsed = self.pu(LANGUAGE_CODE_EN,
                         "gen 1 v 1 - 2")
        self._test_verse_range(parsed)

    def _test_verse_range(self, parsed):
        self.assertEqual(parsed.book_number, 0)
        self.assertEqual(parsed.book_name, "Genesis")
        self.assertEqual(parsed.start_chapter, 1)
        self.assertEqual(parsed.end_chapter, 1)
        self.assertEqual(parsed.start_verse, 1)
        self.assertEqual(parsed.end_verse, 2)
        self.assertEqual(parsed.is_single_verse(), False)
        self.assertEqual(parsed.is_whole_book(), False)
        self.assertEqual(parsed.is_whole_chapter(), False)

        start = parsed.get_start()
        self.assertEqual(start.start_chapter, 1)
        self.assertEqual(start.end_chapter, 1)
        self.assertEqual(start.start_verse, 1)
        self.assertEqual(start.end_verse, 1)

        end = parsed.get_end()
        self.assertEqual(end.start_chapter, 1)
        self.assertEqual(end.end_chapter, 1)
        self.assertEqual(end.start_verse, 2)
        self.assertEqual(end.end_verse, 2)

    def test_verse_range_2_strict(self):
        parsed = self.pv(LANGUAGE_CODE_EN,
                         "Genesis 1:2-3:4")
        self._test_verse_range_2(parsed)

    def test_verse_range_2_loose(self):
        parsed = self.pu(LANGUAGE_CODE_EN,
                         "gen 1v2 - 3v4")
        self._test_verse_range_2(parsed)

    def _test_verse_range_2(self, parsed):
        self.assertEqual(parsed.start_chapter, 1)
        self.assertEqual(parsed.end_chapter, 3)
        self.assertEqual(parsed.start_verse, 2)
        self.assertEqual(parsed.end_verse, 4)
        self.assertEqual(parsed.is_single_verse(), False)
        self.assertEqual(parsed.is_whole_book(), False)
        self.assertEqual(parsed.is_whole_chapter(), False)

        start = parsed.get_start()
        self.assertEqual(start.start_chapter, 1)
        self.assertEqual(start.end_chapter, 1)
        self.assertEqual(start.start_verse, 2)
        self.assertEqual(start.end_verse, 2)

        end = parsed.get_end()
        self.assertEqual(end.start_chapter, 3)
        self.assertEqual(end.end_chapter, 3)
        self.assertEqual(end.start_verse, 4)
        self.assertEqual(end.end_verse, 4)

    def test_from_start_and_end(self):
        parsed = self.pv(LANGUAGE_CODE_EN,
                         "Genesis 1:2-3:4")
        combined = ParsedReference.from_start_and_end(parsed.get_start(),
                                                      parsed.get_end())
        self.assertEqual(parsed, combined)

        parsed2 = self.pv(LANGUAGE_CODE_EN,
                          "Genesis 1:1")
        combined2 = ParsedReference.from_start_and_end(parsed2.get_start(),
                                                       parsed2.get_end())
        self.assertEqual(parsed2, combined2)

        parsed3 = self.pv(LANGUAGE_CODE_EN,
                          "Genesis 1")
        combined3 = ParsedReference.from_start_and_end(parsed3.get_start(),
                                                       parsed3.get_end())
        self.assertEqual(parsed3, combined3)

    def test_parse_books(self):
        # Check that the book names parse back to themselves.
        for lang in LANGUAGES:
            for book in get_bible_books(lang.code):
                r = self.pu(lang.code, book,
                            allow_whole_book=True).canonical_form()
                book_number = get_bible_book_number(lang.code, book)
                if is_single_chapter_book(book_number):
                    self.assertEqual(r, book + " 1")
                else:
                    self.assertEqual(r, book)

    def test_single_chapter_books(self):
        parsed = self.pu(LANGUAGE_CODE_EN, "Jude")
        self.assertEqual(parsed.canonical_form(), "Jude 1")
        self.assertEqual(parsed.is_whole_book(), True)
        self.assertEqual(parsed.is_whole_chapter(), True)

    def test_constraints(self):
        self.assertEqual(self.pu(LANGUAGE_CODE_EN, "Matt 1",
                                 allow_whole_book=False,
                                 allow_whole_chapter=True).canonical_form(),
                         "Matthew 1")
        self.assertEqual(self.pu(LANGUAGE_CODE_EN, "Matt 1",
                                 allow_whole_book=False,
                                 allow_whole_chapter=False),
                         None)
        self.assertEqual(self.pu(LANGUAGE_CODE_EN, "Matt",
                                 allow_whole_book=True,
                                 allow_whole_chapter=True).canonical_form(),
                         "Matthew")
        self.assertEqual(self.pu(LANGUAGE_CODE_EN, "Matt",
                                 allow_whole_book=False,
                                 allow_whole_chapter=True),
                         None)
        self.assertEqual(self.pu(LANGUAGE_CODE_EN, "Jude",
                                 allow_whole_book=False,
                                 allow_whole_chapter=True).canonical_form(),
                         "Jude 1")

    def test_invalid_references(self):
        with override('en'):
            self.assertRaises(InvalidVerseReference,
                              lambda: self.pv(LANGUAGE_CODE_EN, "Matthew 2:1-1:2"))
            # Even with loose parsing, we still propagage InvalidVerseReference, so
            # that the front end code (e.g. quick_find) can recognise that the user
            # tried to enter a verse reference.
            self.assertRaises(InvalidVerseReference,
                              lambda: self.pu(LANGUAGE_CODE_EN, "Matthew 2:1-1:2"))

    def test_turkish_reference_parsing(self):
        tests = [
            # Different numbering styles for book names:
            ("1. Timoteos 3:16", "1. Timoteos 3:16"),
            ("1 Timoteos 3:16", "1. Timoteos 3:16"),
            ("1Timoteos 3:16", "1. Timoteos 3:16"),
            ("1tim 3.16", "1. Timoteos 3:16"),
            # Apostrophes optional
            ("Yasanın Tekrarı 1", "Yasa'nın Tekrarı 1"),
            # Turkish people often miss out accents or use the wrong kind of 'i'
            # etc. when typing, especially as keyboards may not support correct
            # characters.
            ("YARATILIS 2:3", "Yaratılış 2:3"),
            ("YARATİLİS 2:3", "Yaratılış 2:3"),
            ("yaratilis 2:3", "Yaratılış 2:3"),
            ("colde sayim 4:5", "Çölde Sayım 4:5"),
            ("EYÜP 1", "Eyüp 1"),
        ]
        for ref, output in tests:
            self.assertEqual(self.pu(LANGUAGE_CODE_TR, ref).canonical_form(),
                             output,
                             f"Failure parsing '{ref}'")

        self.assertEqual(normalize_reference_input_turkish('  ÂâİIiıÇçŞşÖöÜüĞğ  '),
                         'aaiiiiccssoouugg')

    def test_to_list(self):
        def assertListEqual(ref, ref_list):
            parsed_ref = self.pv('en', ref)
            self.assertEqual(parsed_ref.to_list(),
                             [self.pv('en', r) for r in ref_list])

        assertListEqual('Genesis 1:1', ['Genesis 1:1'])
        assertListEqual('Genesis 1:1-2', ['Genesis 1:1', 'Genesis 1:2'])
        assertListEqual('Genesis 1:30-2:2', [
            'Genesis 1:30',
            'Genesis 1:31',
            'Genesis 2:1',
            'Genesis 2:2',
        ])
        assertListEqual('Genesis 1:30-31', [
            'Genesis 1:30',
            'Genesis 1:31',
        ])
        assertListEqual('Psalm 23', [
            'Psalm 23:1',
            'Psalm 23:2',
            'Psalm 23:3',
            'Psalm 23:4',
            'Psalm 23:5',
            'Psalm 23:6',
        ])
        assertListEqual('Jude 1:25', [
            'Jude 1:25',
        ])


class MockVersion:
    def __init__(self, language_code):
        self.language_code = language_code


class MockUVS:
    def __init__(self, localized_reference, language_code=LANGUAGE_CODE_EN):
        self.localized_reference = localized_reference
        self.version = MockVersion(language_code=language_code)


class GetPassageSectionsTests(unittest2.TestCase):

    def test_empty(self):
        uvs_list = [MockUVS('Genesis 1:1'),
                    MockUVS('Genesis 1:2')]
        sections = get_passage_sections(uvs_list, '')
        self.assertEqual([[uvs.localized_reference for uvs in section]
                          for section in sections],
                         [["Genesis 1:1", "Genesis 1:2"]])

    def test_simple_verse_list(self):
        uvs_list = [MockUVS('Genesis 1:1'),
                    MockUVS('Genesis 1:2'),
                    MockUVS('Genesis 1:3'),
                    MockUVS('Genesis 1:4'),
                    MockUVS('Genesis 1:5')]

        sections = get_passage_sections(uvs_list, 'BOOK0 1:1,BOOK0 1:4')
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

        sections = get_passage_sections(uvs_list, 'BOOK0 1:4')
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

        sections = get_passage_sections(uvs_list, 'BOOK0 1:13,BOOK0 2:2,BOOK0 2:4')
        self.assertEqual([[uvs.localized_reference for uvs in section]
                          for section in sections],
                         [["Genesis 1:11", "Genesis 1:12"],
                          ["Genesis 1:13", "Genesis 2:1"],
                          ["Genesis 2:2", "Genesis 2:3"],
                          ["Genesis 2:4", "Genesis 2:5"],
                          ])

    def test_combo_and_merged_verses_1(self):
        # For this API, combo verses and merged verses are the same
        # (they appear as verse refs spanning multiple items)
        # so we can combine tests additional tests
        uvs_list = [MockUVS('Genesis 1:1'),
                    MockUVS('Genesis 1:2'),
                    MockUVS('Genesis 1:3-4'),
                    MockUVS('Genesis 1:5')]

        sections = get_passage_sections(uvs_list, 'BOOK0 1:3')
        self.assertEqual([[uvs.localized_reference for uvs in section]
                          for section in sections],
                         [["Genesis 1:1", "Genesis 1:2"],
                          ["Genesis 1:3-4", "Genesis 1:5"]])

    def test_combo_and_merged_verses_2(self):
        uvs_list = [MockUVS('Genesis 1:1'),
                    MockUVS('Genesis 1:2'),
                    MockUVS('Genesis 1:3-4'),
                    MockUVS('Genesis 1:5')]

        sections = get_passage_sections(uvs_list, 'BOOK0 1:4')
        # For this case we make an arbitrary decision to ignore breaks
        # that occur in the middle of a merged/combo verse. In reality
        # this is just a corner case that is very unlikely to ever occur.
        self.assertEqual([[uvs.localized_reference for uvs in section]
                          for section in sections],
                         [["Genesis 1:1",
                           "Genesis 1:2",
                           "Genesis 1:3-4",
                           "Genesis 1:5"]])


class IsContinuousSetTests(BibleVersesMixin, TestBase):
    def test_is_continuous_set_1(self):
        verse_list = list(self.KJV.verse_set
                          .filter(localized_reference__in=[
                              'Genesis 1:1',
                              'Genesis 1:2',
                              'Genesis 1:3'])
                          .order_by('bible_verse_number'))
        self.assertTrue(is_continuous_set(verse_list))

    def test_is_continuous_set_2(self):
        verse_list = list(self.KJV.verse_set
                          .filter(localized_reference__in=[
                              'Genesis 1:1',
                              'Genesis 1:2',
                              'Genesis 1:7'])
                          .order_by('bible_verse_number'))
        self.assertFalse(is_continuous_set(verse_list))

    def test_is_continuous_set_3(self):
        verse_list = list(self.TCL02.verse_set
                          .filter(localized_reference__in=[
                              'Romalılar 3:24',
                              'Romalılar 3:25-26',
                              'Romalılar 3:27'])
                          .order_by('bible_verse_number'))
        self.assertTrue(is_continuous_set(verse_list))

    def test_is_continuous_set_4(self):
        verse_list = list(self.TCL02.verse_set
                          .filter(localized_reference__in=[
                              'Yuhanna 3:16',
                              'Romalılar 3:24',
                              'Romalılar 3:27'])
                          .order_by('bible_verse_number'))
        self.assertFalse(is_continuous_set(verse_list))


class UserVerseStatusTests(RequireExampleVerseSetsMixin, AccountTestMixin, TestBase):
    # Many other tests for this model are found in test_identity

    def test_passage_and_section_localized_reference(self):
        # Setup to create UVSs
        identity, account = self.create_account()
        vs = VerseSet.objects.get(name="Psalm 23")
        vs.breaks = "BOOK18 23:4"
        vs.save()
        identity.add_verse_set(vs)

        uvs = identity.verse_statuses.get(localized_reference='Psalm 23:2')

        self.assertEqual(uvs.passage_localized_reference, 'Psalm 23:1-6')
        self.assertEqual(uvs.section_localized_reference, 'Psalm 23:1-3')

    def test_passage_and_section_localized_reference_merged(self):
        # Setup to create UVSs
        identity, account = self.create_account(version_slug='TCL02')
        vs = self.create_verse_set(
            VerseSetType.PASSAGE,
            "Romans 3:24-25", "", "r",
            ["Romans 3:24", "Romans 3:25"])
        identity.add_verse_set(vs)

        # Get a single verse and check its section/passage
        uvs = identity.verse_statuses.get(localized_reference='Romalılar 3:24')

        # Should be expanded to account for merged verse.
        self.assertEqual(uvs.section_localized_reference, 'Romalılar 3:24-26')
        self.assertEqual(uvs.passage_localized_reference, 'Romalılar 3:24-26')

        # Other tests for the underlying functionality are in GetPassageSectionsTests

    def test_search_by_parsed_ref_single(self):
        identity, account = self.create_account()
        identity.add_verse_set(VerseSet.objects.get(name="Psalm 23"))

        self.assertEqual(
            len(identity.verse_statuses.search_by_parsed_ref(
                parse_validated_localized_reference("en", "Psalm 23:1"))),
            1)

    def test_search_by_parsed_ref_range(self):
        identity, account = self.create_account()
        identity.add_verse_set(VerseSet.objects.get(name="Psalm 23"))

        self.assertEqual(
            len(identity.verse_statuses.search_by_parsed_ref(
                parse_validated_localized_reference("en", "Psalm 23:1-3"))),
            3)

    def test_search_by_parsed_ref_chapter(self):
        identity, account = self.create_account()
        identity.add_verse_set(VerseSet.objects.get(name="Psalm 23"))

        self.assertEqual(
            len(identity.verse_statuses.search_by_parsed_ref(
                parse_validated_localized_reference("en", "Psalm 23"))),
            6)

    def test_search_by_parsed_ref_combo(self):
        identity, account = self.create_account()
        identity.add_verse_choice('Psalm 23:1-2')

        self.assertEqual(
            len(identity.verse_statuses.search_by_parsed_ref(
                parse_validated_localized_reference("en", "Psalm 23:1"))),
            1)

        self.assertEqual(
            len(identity.verse_statuses.search_by_parsed_ref(
                parse_validated_localized_reference("en", "Psalm 23:1-2"))),
            1)

        self.assertEqual(
            len(identity.verse_statuses.search_by_parsed_ref(
                parse_validated_localized_reference("en", "Psalm 23:1-3"))),
            1)

        self.assertEqual(
            len(identity.verse_statuses.search_by_parsed_ref(
                parse_unvalidated_localized_reference("en", "Psalm 23:2-3"))),
            1)

        self.assertEqual(
            len(identity.verse_statuses.search_by_parsed_ref(
                parse_unvalidated_localized_reference("en", "Psalm 23:3-4"))),
            0)

    def test_search_by_parsed_ref_different_language(self):
        identity, account = self.create_account()
        identity.add_verse_choice('Psalm 23:1')
        identity.add_verse_choice('Psalm 23:2')

        self.assertEqual(
            len(identity.verse_statuses.search_by_parsed_ref(
                parse_validated_localized_reference("tr", "Mezmur 23:1"))),
            1)

        self.assertEqual(
            len(identity.verse_statuses.search_by_parsed_ref(
                parse_validated_localized_reference("tr", "Mezmur 23"))),
            2)


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

    def test_split_into_words_trailing_newline(self):
        text = 'RAB çobanımdır, \n Eksiğim olmaz. \n'
        self.assertEqual(split_into_words(text),
                         ['RAB', 'çobanımdır,\n', 'Eksiğim', 'olmaz.\n'])

    def test_split_into_words_turkish(self):
        text = "Düşmanı, öç alanı yok etmek için."
        self.assertEqual(split_into_words(text),
                         ['Düşmanı,', 'öç', 'alanı', 'yok', 'etmek', 'için.'])


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
                             first_verse_number=16,
                             last_verse_number=16,
                             bible_verse_number=26136)
        esv.verse_set.create(localized_reference='John 3:17',
                             book_number=42,
                             chapter_number=3,
                             first_verse_number=17,
                             last_verse_number=17,
                             bible_verse_number=26137)
        esv.verse_set.create(localized_reference='John 5:4',
                             book_number=42,
                             chapter_number=5,
                             first_verse_number=4,
                             last_verse_number=4,
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
        verses = self.esv.get_verse_list('John 3:16')
        text = self.JOHN_316_TEXT
        self.assertEqual(verses[0].text, text)
        self._assert_john316_correct()

    def test_combo_verses(self):
        d = self.esv.get_verses_by_localized_reference_bulk(['John 5:4', 'John 3:16-17'])
        self.assertEqual(d['John 5:4'].text, "")
        self.assertEqual(d['John 3:16-17'].text, self.JOHN_316_TEXT + " " + self.JOHN_317_TEXT)

    def test_get_verse_list_missing(self):
        verses = self.esv.get_verse_list('John 5:4')
        self.assertEqual(verses[0].text, '')

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
