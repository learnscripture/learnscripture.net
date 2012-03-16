from __future__ import absolute_import

from django.core.urlresolvers import reverse
from selenium.webdriver.support.ui import Select

from accounts.models import Identity
from bibleverses.models import VerseSet

from .base import LiveServerTests

class ChooseTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def test_search(self):
        driver = self.driver
        driver.get(self.live_server_url + reverse('choose'))
        driver.find_element_by_id('id-search-input').send_keys('gospel')
        driver.find_element_by_id('id-search-btn').click()

        self.wait_until_loaded('body')
        self.assertIn("Basic Gospel", driver.page_source)
        self.assertNotIn("Bible 101", driver.page_source)

    def test_popularity_tracking(self):
        driver = self.driver
        driver.get(self.live_server_url + reverse('choose'))

        vs_id = 1
        self.assertEqual(VerseSet.objects.get(id=vs_id).popularity, 0)
        driver.find_element_by_id("id-learn-verseset-btn-%d" % vs_id).click()
        self.set_preferences()
        self.wait_until_loaded('body')
        self.assertEqual(VerseSet.objects.get(id=vs_id).popularity, 1)

    def test_double_choose(self):
        driver = self.driver
        driver.get(self.live_server_url + reverse('choose'))

        vs = VerseSet.objects.get(name="Psalm 23")
        driver.find_element_by_id("id-learn-verseset-btn-%d" % vs.id).click()

        self.set_preferences()
        self.wait_until_loaded('body')

        # Change version:
        Select(driver.find_element_by_id("id-version-select")).select_by_visible_text("NET")

        self.wait_for_ajax()

        identity = Identity.objects.get()

        self.assertEqual(vs.verse_choices.count(),
                         identity.verse_statuses.filter(ignored=False).count())

        # Choose again
        driver.get(self.live_server_url + reverse('choose'))
        driver.find_element_by_id("id-learn-verseset-btn-%d" % vs.id).click()

        self.assertEqual(vs.verse_choices.count(),
                         identity.verse_statuses.filter(ignored=False).count())

    def test_choose_individual_verse(self):
        driver = self.driver
        driver.get(self.live_server_url + reverse('choose'))
        driver.find_element_by_css_selector("a[href='#id-tab-individual']").click()
        Select(driver.find_element_by_id("id_book")).select_by_visible_text("John")
        driver.find_element_by_id("id_chapter").send_keys("3")
        driver.find_element_by_id("id_start_verse").send_keys("16")
        driver.find_element_by_css_selector("input[name=lookup]").click()
        self.wait_until_loaded('body')

        self.assertIn("For this is the way God loved the world", driver.page_source)

        driver.find_element_by_css_selector("#id-tab-individual input[value=Learn]").click()
        self.set_preferences()
        self.wait_until_loaded('body')
        self.wait_for_ajax()
        self.assertEqual(driver.find_element_by_id("id-verse-title").text, u"John 3:16")
