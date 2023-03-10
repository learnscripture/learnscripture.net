import time

from accounts.models import TestingMethod
from events.models import Event, EventType

from .base import CatechismsMixin, FullBrowserTest


class CatechismTests(CatechismsMixin, FullBrowserTest):
    def test_list(self):
        self.get_url("catechisms")
        self.assertTextPresent("Westminster Shorter")
        self.assertTextPresent("4 question/answer pairs")

    def test_learn(self):
        identity, account = self.create_account(testing_method=TestingMethod.FULL_WORDS)
        self.login(account)
        self.get_url("catechisms")
        self.click(".btn.primary[type=submit]")
        assert self.get_element_text("#id-verse-header h2") == "Q1. What is the chief end of man?"

        # Do some stuff on 'learn' page, for the sake of some basic testing
        # of learning page, and the STARTED_LEARNING_CATECHISM event.

        # Do the reading:
        for i in range(0, 9):
            self.click("#id-next-btn")

        for word in "Man's chief end is to glorify God and to enjoy him forever".split(" "):
            self.fill({"#id-typing": word + " "})

        self.wait_for_ajax()

        time.sleep(0.5)
        assert Event.objects.filter(event_type=EventType.STARTED_LEARNING_CATECHISM).count() == 1
