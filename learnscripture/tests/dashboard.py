from __future__ import absolute_import

from datetime import timedelta

from django.core.urlresolvers import reverse
from django.db.models import F
from django.utils import timezone

from accounts import memorymodel
from accounts.models import Identity, Notice, TestingMethod, FREE_TRIAL_LENGTH_DAYS
from bibleverses.models import VerseSet, TextVersion, StageType, MemoryStage
from .base import LiveServerTests


class DashboardTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json',
                'test_catechisms.json']

    def test_redirect(self):
        driver = self.driver
        self.get_url('dashboard')
        self.assertTrue(driver.current_url.endswith(reverse('choose')))

    def setup_identity(self):
        ids = list(Identity.objects.all())
        driver = self.driver
        self.get_url('preferences')
        self.wait_until_loaded('body')
        self.set_preferences()
        # This should have created an Identity
        i = Identity.objects.exclude(id__in=[i.id for i in ids]).get()
        i.default_bible_version = TextVersion.objects.get(slug='NET')
        i.testing_method = TestingMethod.FULL_WORDS
        i.save()
        return i

    def test_learn_queue(self):
        # This combines a bunch of tests, it's easier to avoid a lot of
        # repetition that way.

        driver = self.driver
        i = self.setup_identity()
        vs = VerseSet.objects.get(slug='bible-101')
        i.add_verse_set(vs)

        # Test verses appear on dashboard
        self.get_url('dashboard')
        self.assertIn('John 3:16', driver.page_source)
        self.assertIn('John 14:6', driver.page_source)

        # Test clicking 'Start learning' for learn queue
        driver.find_element_by_css_selector('input[name=learnbiblequeue]').click()
        self.wait_until_loaded('body')
        self.assertTrue(driver.current_url.endswith(reverse('learn')))

        self.wait_for_ajax()
        self.assertEqual(u"John 3:16", driver.find_element_by_id('id-verse-title').text)

        # Learn one verse (otherwise we are back to dashboard redirecting us)
        i.record_verse_action('John 3:16', 'NET', StageType.TEST, accuracy=1.0)

        # Test clicking 'Clear queue'
        self.get_url('dashboard')
        driver.find_element_by_css_selector('input[name=clearbiblequeue]').click()
        alert = driver.switch_to_alert()
        alert.accept()
        self.wait_until_loaded('body')

        # Since we cleared the queue, shouldn't have John 14:6 now
        self.assertTrue(driver.current_url.endswith(reverse('dashboard')))
        self.assertNotIn('John 14:6', driver.page_source)

    def test_learn_passage(self):
        # As above, combine several tests as a story, for simplicity
        i = self.setup_identity()

        # This is to stop redirecting behaviour due to an empty dashboard
        i.add_verse_set(VerseSet.objects.get(slug='bible-101'))

        # Add a passage
        vs = VerseSet.objects.get(slug='psalm-23')
        i.add_verse_set(vs)

        driver = self.driver

        # Test dashboard text
        self.get_url('dashboard')
        self.assertIn('Psalm 23', driver.page_source)

        # Test 'Continue learning' button
        driver.find_element_by_id('id-learnpassage-btn-%d' % vs.id).click()
        self.wait_until_loaded('body')
        self.assertTrue(driver.current_url.endswith(reverse('learn')))
        self.wait_for_ajax()
        self.assertEqual(u"Psalm 23:1", driver.find_element_by_id('id-verse-title').text)

        # Test 'Cancel learning' button
        self.get_url('dashboard')
        driver.find_element_by_id('id-cancelpassage-btn-%d' % vs.id).click()
        alert = driver.switch_to_alert()
        alert.accept()
        self.wait_until_loaded('body')
        self.assertNotIn('Psalm 23', driver.page_source)

    hide_browser = False

    def test_learn_catechism(self):
        driver = self.driver
        i = self.setup_identity()
        i.add_catechism(TextVersion.objects.get(slug='WSC'))
        self.get_url('dashboard')
        self.assertIn("You've got 4 catechism questions in your queue for learning",
                      driver.page_source)

        driver.find_element_by_css_selector('input[name=learncatechismqueue]').click()
        self.wait_until_loaded('body')
        self.assertTrue(driver.current_url.endswith(reverse('learn')))

        self.wait_for_ajax()
        self.assertEqual(u"Q1. What is the chief end of man?", driver.find_element_by_id('id-verse-title').text)

        i.record_verse_action('Q1', 'WSC', StageType.TEST, accuracy=1.0)

        # Test clicking 'Clear queue'
        self.get_url('dashboard')
        driver.find_element_by_css_selector('input[name=clearcatechismqueue]').click()
        alert = driver.switch_to_alert()
        alert.accept()
        self.wait_until_loaded('body')

        # Since we cleared the queue, shouldn't have anything about catechisms now
        self.assertTrue(driver.current_url.endswith(reverse('dashboard')))
        self.assertNotIn('catechism', driver.page_source)


    def test_revise_one_section(self):
        i = self.setup_identity()

        # Add a passage
        vs = VerseSet.objects.get(slug='psalm-23')
        vs.breaks = "23:4"
        vs.save()
        i.add_verse_set(vs)

        # Get to 'group testing' stage
        i.verse_statuses.update(strength=memorymodel.STRENGTH_FOR_GROUP_TESTING + 0.01,
                                last_tested=timezone.now() - timedelta(days=10),
                                next_test_due=timezone.now() - timedelta(days=1),
                                memory_stage=MemoryStage.TESTED)

        driver = self.driver

        self.get_url('dashboard')
        self.assertIn('Psalm 23', driver.page_source) # sanity check

        btn = driver.find_element_by_css_selector('input[value="Revise one section"]')
        self.assertEqual(btn.get_attribute('name'), 'revisepassagenextsection')
        btn.click()

        self.wait_until_loaded('body')
        self.wait_for_ajax()
        self.assertIn("Psalm 23:1", driver.page_source)

        # Skip through
        def skip():
            driver.find_element_by_id("id-verse-dropdown").click()
            driver.find_element_by_link_text("Skip this").click()
            self.wait_for_ajax()
        skip()
        self.assertIn("Psalm 23:2", driver.page_source)
        skip()
        self.assertIn("Psalm 23:3", driver.page_source)
        skip()
        self.wait_until_loaded('body')

        # Should be back at dashboard
        self.assertTrue(driver.current_url.endswith(reverse('dashboard')))

    def test_home_dashboard_routing(self):
        ids = list(Identity.objects.all())
        driver = self.driver
        driver.get(self.live_server_url + "/")
        e = driver.find_element_by_css_selector('a.btn.large')
        self.assertTrue(e.get_attribute('href').endswith(reverse('dashboard')))
        e.click()
        self.assertTrue(driver.current_url.endswith(reverse('choose')))
        self.assertEqual(Identity.objects.exclude(id__in=[i.id for i in ids]).count(), 0)

    def test_notices_expire(self):
        # This could be tested on any page, but this is an obvious example.
        identity, account = self.create_account()
        self.login(account)
        account.add_html_notice("Hello you crazy guy!")

        self.assertEqual(identity.notices.all()[0].seen, None)

        driver = self.driver

        self.get_url('dashboard')
        self.assertIn("Hello you crazy guy!", driver.page_source)

        self.assertNotEqual(identity.notices.all()[0].seen, None)

        # Move database into 'past'
        Notice.objects.update(seen = F('seen') - timedelta(days=10))

        self.get_url('dashboard')
        self.assertNotIn("Hello you crazy guy!", driver.page_source)
