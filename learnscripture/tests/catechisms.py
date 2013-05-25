from __future__ import absolute_import

from django.core.urlresolvers import reverse

from events.models import Event, EventType

from .base import LiveServerTests


class CatechismTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_catechisms.json']

    def test_list(self):
        driver = self.driver
        self.get_url('catechisms')
        self.assertIn("Westminster Shorter", driver.page_source)
        self.assertIn("4 question/answer pairs", driver.page_source)

    def test_learn(self):
        driver = self.driver
        identity, account = self.create_account()
        self.login(account)
        self.get_url('catechisms')
        driver.find_element_by_css_selector("input[value=Learn]").click()
        self.set_preferences()
        self.wait_until_loaded('body')
        self.wait_for_ajax()
        self.assertEqual(driver.find_element_by_css_selector("#id-verse-title").text,
                         "Q1. What is the chief end of man?")

        # Do some stuff on 'learn' page, for the sake of some basic testing
        # of learning page, and the STARTED_LEARNING_CATECHISM event.

        # Do the reading:
        for i in range(0, 9):
            driver.find_element_by_css_selector("#id-next-btn").click()

        for word in "Man's chief end is to glorify God and to enjoy him forever".split(" "):
            self.driver.find_element_by_css_selector("#id-typing").send_keys(word + " ")

        self.wait_for_ajax()

        self.assertEqual(Event.objects
                         .filter(event_type=EventType.STARTED_LEARNING_CATECHISM)
                         .count(),
                         1)
