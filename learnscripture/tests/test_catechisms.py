import time

from events.models import Event, EventType

from .base import FullBrowserTest


class CatechismTests(FullBrowserTest):

    fixtures = ['test_bible_versions.json', 'test_catechisms.json']

    def test_list(self):
        self.get_url('catechisms')
        self.assertTextPresent("Westminster Shorter")
        self.assertTextPresent("4 question/answer pairs")

    def test_learn(self):
        identity, account = self.create_account()
        self.login(account)
        self.get_url('catechisms')
        self.click("input[value=Learn]")
        self.assertEqual(self.get_element_text("#id-verse-header h2"),
                         "Q1. What is the chief end of man?")

        # Do some stuff on 'learn' page, for the sake of some basic testing
        # of learning page, and the STARTED_LEARNING_CATECHISM event.

        # Do the reading:
        for i in range(0, 9):
            self.click("#id-next-btn")

        for word in "Man's chief end is to glorify God and to enjoy him forever".split(" "):
            self.fill({"#id-typing": word + " "})

        self.wait_for_ajax()

        time.sleep(0.5)
        self.assertEqual(Event.objects
                         .filter(event_type=EventType.STARTED_LEARNING_CATECHISM)
                         .count(),
                         1)
