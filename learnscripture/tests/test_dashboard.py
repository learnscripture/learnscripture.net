from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from time_machine import travel

import accounts.memorymodel
from accounts.models import Identity
from bibleverses.models import MemoryStage, StageType, TextVersion, VerseSet

from .base import CatechismsMixin, FullBrowserTest, WebTestBase
from .test_bibleverses import RequireExampleVerseSetsMixin


class DashboardTestsBase(RequireExampleVerseSetsMixin, CatechismsMixin):

    databases = {"default", "wordsuggestions"}

    def test_redirect(self):
        self.get_url("dashboard")
        self.assertUrlsEqual(reverse("login"))

    def assert_learning_localized_reference(self, ref):
        self.assertUrlsEqual(reverse("learn"))
        if self.is_full_browser_test:
            assert ref == self.get_element_text("#id-verse-header h2")
        else:
            json = self.app.get(reverse("learnscripture.api.versestolearn")).json
            verse_statuses = json["verse_statuses"]
            verse_data = [d for d in verse_statuses if d["learn_order"] == 0][0]
            assert ref == verse_data["title_text"]

    def click_clear_learning_queue_btn(self, verse_set_id):
        if verse_set_id:
            self.click_and_confirm(f"#id-learning-queue-verse-set-{verse_set_id} [name=clearbiblequeue]")
        else:
            self.click_and_confirm("#id-learning-queue-non-verse-set [name=clearbiblequeue]")

    def click_cancel_passage_btn(self, verse_set_id, version_id):
        self.click_and_confirm("#id-cancelpassage-btn-%d-%d" % (verse_set_id, version_id))

    def click_clear_catechsim_queue_btn(self):
        self.click_and_confirm("[name=clearcatechismqueue]")

    def test_learn_queue(self):
        # This combines a bunch of tests, it's easier to avoid a lot of
        # repetition that way.
        i = self.setup_identity()

        # Add a verse set
        vs = VerseSet.objects.get(slug="bible-101")
        i.add_verse_set(vs)

        # And an individual verse
        i.add_verse_choice("Psalm 23:2")

        # Test verses appear on dashboard
        self.get_url("dashboard")
        self.assertTextPresent("John 3:16")
        self.assertTextPresent("John 14:6")
        self.assertTextPresent("Psalm 23:2")

        # Test click 'Start learning' for 'Bible 101' verse set
        self.assertTextPresent("Bible 101")
        self.submit(f"#id-learning-queue-verse-set-{vs.id} [name=learnbiblequeue]")
        self.assert_learning_localized_reference("John 3:16")

        # Learn one verse (otherwise we are back to dashboard redirecting us)
        i.record_verse_action("John 3:16", "NET", StageType.TEST, accuracy=1.0)

        self.get_url("dashboard")
        # Test clicking 'Start learning' for general queue
        self.submit("#id-learning-queue-non-verse-set [name=learnbiblequeue]")
        self.assert_learning_localized_reference("Psalm 23:2")

        # Test clicking 'Clear queue'
        self.get_url("dashboard")
        self.click_clear_learning_queue_btn(vs.id)

        # Since we cleared the queue, shouldn't have John 14:6 now
        self.assertUrlsEqual(reverse("dashboard"))
        self.assertTextAbsent("John 14:6")

        # but should still have Psalm 23:2
        self.assertTextPresent("Psalm 23:2")

        # Click the other 'Clear queue' button
        self.click_clear_learning_queue_btn(None)

        self.assertTextAbsent("Psalm 23:2")

    def test_learn_passage(self):
        # As above, combine several tests as a story, for simplicity
        i = self.setup_identity()

        # This is to stop redirecting behaviour due to an empty dashboard
        i.add_verse_set(VerseSet.objects.get(slug="bible-101"))

        # Add a passage
        vs = VerseSet.objects.get(slug="psalm-23")
        i.add_verse_set(vs)

        # Test dashboard text
        self.get_url("dashboard")
        self.assertTextPresent("Psalm 23")

        # Test 'Continue learning' button
        self.submit("#id-learnpassage-btn-%d-%d" % (vs.id, i.default_bible_version.id))
        self.assert_learning_localized_reference("Psalm 23:1")

        # Test 'Cancel learning' button
        self.get_url("dashboard")
        self.click_cancel_passage_btn(vs.id, i.default_bible_version.id)
        self.assertTextAbsent("Psalm 23")

    def test_learn_catechism(self):
        i = self.setup_identity()
        i.add_catechism(TextVersion.objects.get(slug="WSC"))
        self.get_url("dashboard")
        self.assertTextPresent("You've queued this catechism for learning, 4 questions total")

        self.submit("[name=learncatechismqueue]")
        self.assert_learning_localized_reference("Q1. What is the chief end of man?")

    def test_cancel_catechsim(self):
        # Test clicking 'Clear queue'
        i = self.setup_identity()
        i.add_catechism(TextVersion.objects.get(slug="WSC"))
        i.record_verse_action("Q1", "WSC", StageType.TEST, accuracy=1.0)

        self.get_url("dashboard")
        sentinel = "Westminster Shorter Catechism 1647"
        self.assertTextPresent(sentinel)
        self.click_clear_catechsim_queue_btn()

        # Since we cleared the queue, shouldn't have anything about catechisms now
        self.assertUrlsEqual(reverse("dashboard"))
        self.assertTextAbsent(sentinel)

    def test_review_one_section(self):
        i = self.setup_identity()

        # Add a passage
        vs = VerseSet.objects.get(slug="psalm-23")
        vs.breaks = "BOOK18 23:4"
        vs.save()
        i.add_verse_set(vs)

        # Get to 'group testing' stage
        i.verse_statuses.update(
            strength=accounts.memorymodel.STRENGTH_FOR_GROUP_TESTING + 0.01,
            last_tested=timezone.now() - timedelta(days=10),
            next_test_due=timezone.now() - timedelta(days=1),
            memory_stage=MemoryStage.TESTED,
        )

        self.get_url("dashboard")
        self.assertTextPresent("Psalm 23")  # sanity check

        self.submit("[name=reviewpassagenextsection]")
        self.assert_learning_localized_reference("Psalm 23:1")

        if self.is_full_browser_test:
            # Skip through
            def skip():
                self.click("#id-verse-options-menu-btn")
                self.click("#id-skip-verse-btn")

            skip()
            self.assertTextPresent("Psalm 23:2")
            skip()
            self.assertTextPresent("Psalm 23:3")
            skip()
            self.wait_until_loaded("body.dashboard-page")

            # Should be back at dashboard
            self.assertUrlsEqual(reverse("dashboard"))

    def test_home_dashboard_routing(self):
        Identity.objects.all().delete()
        self.get_url("home")
        self.follow_link(f"a.btn.large[href=\"{reverse('choose')}\"]")
        self.assertUrlsEqual(reverse("choose"))
        # Getting this far shouldn't create an Identity
        assert Identity.objects.count() == 0

    def test_notices_expire(self):
        # This could be tested on any page, but this is an obvious example.
        identity, account = self.create_account()
        self.login(account)
        account.add_html_notice("Hello you crazy guy!")

        assert identity.notices.all()[0].seen is None

        self.get_url("dashboard")
        self.assertTextPresent("Hello you crazy guy!")

        assert identity.notices.all()[0].seen is not None

        with travel(timezone.now() + timedelta(days=10)):
            self.get_url("dashboard")
            self.assertTextAbsent("Hello you crazy guy!")


class DashboardTestsFB(DashboardTestsBase, FullBrowserTest):
    pass


class DashboardTestsWT(DashboardTestsBase, WebTestBase):
    pass
