from __future__ import absolute_import

from django.core.urlresolvers import reverse

from .base import LiveServerTests


class CatechismListTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_catechisms.json']

    def test_list(self):
        driver = self.driver
        self.get_url('catechisms')
        self.assertIn("Westminster Shorter", driver.page_source)
        self.assertIn("4 question/answer pairs", driver.page_source)

    def test_learn(self):
        driver = self.driver
        self.get_url('catechisms')
        driver.find_element_by_css_selector("input[value=Learn]").click()
        self.set_preferences()
        self.wait_until_loaded('body')
        self.wait_for_ajax()
        self.assertEqual(driver.find_element_by_id('id-verse-title').text,
                         "Q1. What is the chief end of man?")
