from __future__ import absolute_import

from django.core.urlresolvers import reverse

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

