from __future__ import absolute_import

from django.core.urlresolvers import reverse
from selenium.webdriver.support.ui import Select

from accounts.models import Identity
from awards.models import AwardType, TrendSetterAward
from bibleverses.models import VerseSet, Verse, TextVersion
from events.models import Event, EventType

from .base import LiveServerTests

class ChooseTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def test_search(self):
        driver = self.driver
        self.get_url('choose')
        driver.find_element_by_id('id-search-input').send_keys('gospel')
        driver.find_element_by_id('id-search-btn').click()

        self.wait_until_loaded('body')
        self.assertIn("Basic Gospel", driver.page_source)
        self.assertNotIn("Bible 101", driver.page_source)

    def test_verse_set_popularity_tracking(self):
        # Frig a quantity to make test easier
        TrendSetterAward.COUNTS = {1: 1, 2: 10}

        # Need to be logged in for actions to count towards award
        identity, account = self.create_account()
        self.login(account)

        driver = self.driver
        self.get_url('choose')

        vs_id = 1
        self.assertEqual(VerseSet.objects.get(id=vs_id).popularity, 0)
        driver.find_element_by_id("id-learn-verseset-btn-%d" % vs_id).click()
        self.set_preferences()
        self.wait_until_loaded('body')
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

        driver = self.driver
        self.get_url('choose')

        vs = VerseSet.objects.get(name="Psalm 23")
        driver.find_element_by_id("id-learn-verseset-btn-%d" % vs.id).click()

        self.set_preferences()
        self.wait_until_loaded('body')

        # Change version:
        Select(driver.find_element_by_id("id-version-select")).select_by_visible_text("NET")

        self.wait_for_ajax()

        identity = Identity.objects.exclude(id__in=[i.id for i in ids]).get()

        self.assertEqual(vs.verse_choices.count(),
                         identity.verse_statuses.filter(ignored=False).count())

        # Choose again
        self.get_url('choose')
        driver.find_element_by_id("id-learn-verseset-btn-%d" % vs.id).click()

        self.assertEqual(vs.verse_choices.count(),
                         identity.verse_statuses.filter(ignored=False).count())

    def test_choose_individual_verse(self):
        driver = self.driver
        self.get_url('choose')
        driver.find_element_by_css_selector("a[href='#id-tab-individual']").click()

        # Test clicking on the drop downs.
        Select(driver.find_element_by_css_selector("form.quickfind select[name=book]")).select_by_visible_text("John")
        Select(driver.find_element_by_css_selector("form.quickfind select[name=chapter_start]")).select_by_visible_text("3")
        Select(driver.find_element_by_css_selector("form.quickfind select[name=verse_start]")).select_by_visible_text("16")
        driver.find_element_by_css_selector("input[name=lookup]").click()
        self.wait_for_ajax()

        self.assertIn("For this is the way God loved the world", driver.page_source)

        # Check we can actually click on 'Learn' and it works.
        driver.find_element_by_css_selector("#id-tab-individual input[value=Learn]").click()
        self.set_preferences()
        self.wait_until_loaded('body')
        self.wait_for_ajax()
        self.assertEqual(driver.find_element_by_id("id-verse-title").text, u"John 3:16")


    def test_choose_individual_verse_fuzzy(self):
        # Test entering into quick find, and being lazy
        driver = self.driver
        self.get_url('choose')
        driver.find_element_by_css_selector("a[href='#id-tab-individual']").click()

        driver.find_element_by_css_selector('form.quickfind input[name=quick_find]')\
            .send_keys('Gen 1:1')
        Select(driver.find_element_by_css_selector("form.quickfind select[name=version]")).select_by_visible_text("KJV (King James Version)")
        driver.find_element_by_css_selector("input[name=lookup]").click()
        self.wait_for_ajax()

        self.assertIn("In the beginning God", driver.page_source)


    def test_choose_individual_verse_bad_ref(self):
        # Test entering into quick find, and being lazy
        driver = self.driver
        self.get_url('choose')
        driver.find_element_by_css_selector("a[href='#id-tab-individual']").click()

        driver.find_element_by_css_selector('form.quickfind input[name=quick_find]')\
            .send_keys('Gen 100:1')
        Select(driver.find_element_by_css_selector("form.quickfind select[name=version]")).select_by_visible_text("KJV (King James Version)")
        driver.find_element_by_css_selector("input[name=lookup]").click()
        self.wait_for_ajax()

        self.assertNotIn("In the beginning God", driver.page_source)
        self.assertIn("No verses matched 'Genesis 100:1'", driver.page_source)

    def test_choose_individual_by_search(self):
        driver = self.driver
        self.get_url('choose')

        driver.find_element_by_css_selector("a[href='#id-tab-individual']").click()

        driver.find_element_by_css_selector('form.quickfind input[name=quick_find]')\
            .send_keys('firmament evening')
        Select(driver.find_element_by_css_selector("form.quickfind select[name=version]")).select_by_visible_text("KJV (King James Version)")
        driver.find_element_by_css_selector("input[name=lookup]").click()
        self.wait_for_ajax()

        self.assertIn("And God called the <b>firmament</b> Heaven. And the <b>evening</b>", driver.page_source)
