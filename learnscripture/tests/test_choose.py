# -*- coding: utf-8 -*-
from accounts.models import Identity
from awards.models import AwardType, TrendSetterAward
from bibleverses.models import VerseSet
from events.models import Event, EventType

from .base import FullBrowserTest
from .test_bibleverses import RequireExampleVerseSetsMixin
from .test_search import SearchTestsMixin


class ChooseTests(RequireExampleVerseSetsMixin, SearchTestsMixin, FullBrowserTest):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def test_search(self):
        self.get_url('choose')
        self.fill({"#id-search-input": "gospel"})
        self.click("#id-search-btn")

        self.assertTextPresent("Basic Gospel")
        self.assertTextAbsent("Bible 101")

    def test_verse_set_popularity_tracking(self):
        # Frig a quantity to make test easier
        TrendSetterAward.COUNTS = {1: 1, 2: 10}

        # Need to be logged in for actions to count towards award
        identity, account = self.create_account()
        self.login(account)

        self.get_url('choose')

        vs_id = VerseSet.objects.get(name="Bible 101").id
        self.assertEqual(VerseSet.objects.get(id=vs_id).popularity, 0)
        self.click("#id-learn-verseset-btn-%d" % vs_id)
        self.set_preferences()
        self.assertEqual(VerseSet.objects.get(id=vs_id).popularity, 1)

        # Test awards
        vs = VerseSet.objects.get(id=vs_id)
        self.assertEqual(vs.created_by.awards.filter(award_type=AwardType.TREND_SETTER).count(),
                         1)

        # Test events
        self.assertEqual(Event.objects.filter(event_type=EventType.STARTED_LEARNING_VERSE_SET).count(),
                         1)

    def test_double_choose(self):
        ids = list(Identity.objects.all())

        self.get_url('choose')

        vs = VerseSet.objects.get(name="Psalm 23")
        self.click("#id-learn-verseset-btn-%d" % vs.id)

        self.set_preferences()

        # Change version:
        self.fill_by_text({"#id-version-select": "NET"})
        self.wait_for_ajax()

        identity = Identity.objects.exclude(id__in=[i.id for i in ids]).get()

        self.assertEqual(vs.verse_choices.count(),
                         identity.verse_statuses.filter(ignored=False).count())

        # Choose again
        self.get_url('choose')
        self.click("#id-learn-verseset-btn-%d" % vs.id)

        self.assertEqual(vs.verse_choices.count(),
                         identity.verse_statuses.filter(ignored=False).count())

    def test_choose_individual_verse(self):
        self.get_url('choose')
        self.click("a[href='#id-tab-individual']")

        # Test clicking on the drop downs.
        self.fill_by_text({"form.quickfind select[name=book]": "John"})
        self.fill_by_text({"form.quickfind select[name=chapter_start]": "3"})
        self.fill_by_text({"form.quickfind select[name=verse_start]": "16"})
        self.click("input[name=lookup]")

        self.assertTextPresent("For this is the way God loved the world")

        # Check we can actually click on 'Learn' and it works.
        self.click("#id-tab-individual input[value=Learn]")
        self.set_preferences()
        self.assertEqual(self.get_element_text("#id-verse-title"), "John 3:16")

    def test_choose_individual_verse_fuzzy(self):
        # Test entering into quick find, and being lazy
        self.get_url('choose')
        self.click("a[href='#id-tab-individual']")

        self.fill({'form.quickfind input[name=quick_find]': 'Gen 1:1'})
        self.fill({"form.quickfind select[name=version]": "KJV"})
        self.click("input[name=lookup]")

        self.assertTextPresent("In the beginning God")

    def test_choose_individual_verse_bad_ref(self):
        # Test entering into quick find, and being lazy
        self.get_url('choose')
        self.click("a[href='#id-tab-individual']")

        self.fill({'form.quickfind input[name=quick_find]': 'Gen 100:1'})
        self.fill({"form.quickfind select[name=version]": "KJV"})
        self.click("input[name=lookup]")

        self.assertTextAbsent("In the beginning God")
        self.assertTextPresent("No verses matched 'Genesis 100:1'")

    def test_choose_individual_and_change_language(self):
        self.get_url('choose')
        self.click("a[href='#id-tab-individual']")

        # Text is initially in the language of the default version
        self.assertEqual(self.get_element_text("form.quickfind select[name=book] option[value=BOOK0]"),
                         "Genesis")

        # Select verse using drop downs.
        self.fill_by_text({"form.quickfind select[name=book]": "John"})
        self.fill_by_text({"form.quickfind select[name=chapter_start]": "3"})
        self.fill_by_text({"form.quickfind select[name=verse_start]": "16"})
        self.assertEqual(self.get_element_attribute("form.quickfind input[name=quick_find]", "value"),
                         "John 3:16")
        self.click("input[name=lookup]")

        self.assertTextPresent("For this is the way God loved the world")

        self.fill({"form.quickfind select[name=version]": "TCL02"})

        # Search box should change immediately
        self.assertEqual(self.get_element_attribute("form.quickfind input[name=quick_find]", "value"),
                         "Yuhanna 3:16")
        # Drop-downs should change to Turkish
        self.assertEqual(self.get_element_text("form.quickfind select[name=book] option[value=BOOK0]"),
                         "Yaratılış")
        self.click("input[name=lookup]")

        self.assertTextPresent("Çünkü Tanrı dünyayı o kadar çok sevdi ki")

    def test_choose_individual_fuzzy_and_change_language(self):
        self.get_url('choose')
        self.click("a[href='#id-tab-individual']")

        self.fill({'form.quickfind input[name=quick_find]': 'jhn 3:16'})
        self.click("input[name=lookup]")
        self.assertTextPresent("For this is the way God loved the world")

        # # Drop downs should be updated.
        self.assertEqual(self.get_element_text("form.quickfind select[name=book] option:checked"),
                         "John")
        self.assertEqual(self.get_element_attribute("form.quickfind select[name=chapter_start] option:checked", "value"),
                         "3")
        self.assertEqual(self.get_element_attribute("form.quickfind select[name=verse_start] option:checked", "value"),
                         "16")
        self.assertEqual(self.get_element_attribute("form.quickfind select[name=chapter_end] option:checked", "value"),
                         "3")
        self.assertEqual(self.get_element_attribute("form.quickfind select[name=verse_end] option:checked", "value"),
                         "16")
        self.assertEqual(self.get_element_attribute("form.quickfind input[name=quick_find]", "value"),
                         "John 3:16")

        # Now change language.
        self.fill({"form.quickfind select[name=version]": "TCL02"})

        # Search box should change immediately
        self.assertEqual(self.get_element_attribute("form.quickfind input[name=quick_find]", "value"),
                         "Yuhanna 3:16")
        # And drop down
        self.assertEqual(self.get_element_text("form.quickfind select[name=book] option:checked"),
                         "Yuhanna")

        self.click("input[name=lookup]")

        self.assertTextPresent("Çünkü Tanrı dünyayı o kadar çok sevdi ki")

    def test_choose_individual_by_search(self):
        self.get_url('choose')

        self.click("a[href='#id-tab-individual']")

        self.fill({'form.quickfind input[name=quick_find]': 'firmament evening'})
        self.fill({"form.quickfind select[name=version]": "KJV"})
        self.click("input[name=lookup]")

        self.assertTextPresent("And God called the")

    def test_choose_individual_by_search_turkish(self):
        self.get_url('choose')

        self.click("a[href='#id-tab-individual']")

        self.fill({"form.quickfind select[name=version]": "TCL02"})

        # Testing for handling accents and stemming correctly
        self.fill({'form.quickfind input[name=quick_find]': 'övünebilirsiniz'})
        self.click("input[name=lookup]")

        self.assertTextPresent("Öyleyse neyle övünebiliriz?")
        self.assertTextPresent("Romalılar 3:27")
