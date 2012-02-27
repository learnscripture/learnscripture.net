from __future__ import absolute_import

from .base import LiveServerTests

from django.core.urlresolvers import reverse

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
