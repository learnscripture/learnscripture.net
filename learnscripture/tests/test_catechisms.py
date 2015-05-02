from __future__ import absolute_import

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
        identity, account = self.create_account()
        self.login(account)
        self.get_url('catechisms')
        self.click("input[value=Learn]")
        self.set_preferences()
        self.assertEqual(self.find("#id-verse-title").text,
                         "Q1. What is the chief end of man?")

        # Do some stuff on 'learn' page, for the sake of some basic testing
        # of learning page, and the STARTED_LEARNING_CATECHISM event.

        # Do the reading:
        for i in range(0, 9):
            self.click("#id-next-btn")

        for word in "Man's chief end is to glorify God and to enjoy him forever".split(" "):
            self.send_keys("#id-typing", word + " ")

        self.assertEqual(Event.objects
                         .filter(event_type=EventType.STARTED_LEARNING_CATECHISM)
                         .count(),
                         1)
