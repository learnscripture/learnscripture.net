from __future__ import absolute_import

from selenium.webdriver.support.ui import Select

from accounts.models import Identity
from awards.models import AwardType, TrendSetterAward
from bibleverses.models import VerseSet
from events.models import Event, EventType

from .base import LiveServerTests


class ChooseTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def test_search(self):
        driver = self.driver
        self.get_url('choose')
        self.send_keys("#id-search-input", "gospel")
        self.click("#id-search-btn")

        self.assertIn("Basic Gospel", driver.page_source)
        self.assertNotIn("Bible 101", driver.page_source)

    def test_verse_set_popularity_tracking(self):
        # Frig a quantity to make test easier
        TrendSetterAward.COUNTS = {1: 1, 2: 10}

        # Need to be logged in for actions to count towards award
        identity, account = self.create_account()
        self.login(account)

        self.get_url('choose')

        vs_id = 1
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
        Select(self.find("#id-version-select")).select_by_visible_text("NET")

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
        driver = self.driver
        self.get_url('choose')
        self.click("a[href='#id-tab-individual']")

        # Test clicking on the drop downs.
        Select(self.find("form.quickfind select[name=book]")).select_by_visible_text("John")
        Select(self.find("form.quickfind select[name=chapter_start]")).select_by_visible_text("3")
        Select(self.find("form.quickfind select[name=verse_start]")).select_by_visible_text("16")
        self.click("input[name=lookup]")

        self.assertIn("For this is the way God loved the world", driver.page_source)

        # Check we can actually click on 'Learn' and it works.
        self.click("#id-tab-individual input[value=Learn]")
        self.set_preferences()
        self.assertEqual(self.find("#id-verse-title").text, u"John 3:16")

    def test_choose_individual_verse_fuzzy(self):
        # Test entering into quick find, and being lazy
        driver = self.driver
        self.get_url('choose')
        self.click("a[href='#id-tab-individual']")

        self.find('form.quickfind input[name=quick_find]')\
            .send_keys('Gen 1:1')
        Select(self.find("form.quickfind select[name=version]")).select_by_visible_text("KJV (King James Version)")
        self.click("input[name=lookup]")

        self.assertIn("In the beginning God", driver.page_source)

    def test_choose_individual_verse_bad_ref(self):
        # Test entering into quick find, and being lazy
        driver = self.driver
        self.get_url('choose')
        self.click("a[href='#id-tab-individual']")

        self.find('form.quickfind input[name=quick_find]')\
            .send_keys('Gen 100:1')
        Select(self.find("form.quickfind select[name=version]")).select_by_visible_text("KJV (King James Version)")
        self.click("input[name=lookup]")

        self.assertNotIn("In the beginning God", driver.page_source)
        self.assertIn("No verses matched 'Genesis 100:1'", driver.page_source)

    def test_choose_individual_by_search(self):
        driver = self.driver
        self.get_url('choose')

        self.click("a[href='#id-tab-individual']")

        self.find('form.quickfind input[name=quick_find]')\
            .send_keys('firmament evening')
        Select(self.find("form.quickfind select[name=version]")).select_by_visible_text("KJV (King James Version)")
        self.click("input[name=lookup]")

        self.assertIn("And God called the <b>firmament</b> Heaven. And the <b>evening</b>", driver.page_source)
