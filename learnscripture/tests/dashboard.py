from __future__ import absolute_import

from django.core.urlresolvers import reverse

from accounts.models import Identity, TestingMethod
from bibleverses.models import VerseSet, BibleVersion, StageType
from .base import LiveServerTests


class DashboardTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def test_redirect(self):
        driver = self.driver
        driver.get(self.live_server_url + reverse('start'))
        self.assertTrue(driver.current_url.endswith(reverse('choose')))

    def setup_identity(self):
        driver = self.driver
        driver.get(self.live_server_url + reverse('learn'))
        self.wait_until_loaded('body')
        # This should have created an Identity
        i = Identity.objects.get()
        i.default_bible_version = BibleVersion.objects.get(slug='NET')
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
        driver.get(self.live_server_url + reverse('start'))
        self.assertIn('John 3:16', driver.page_source)
        self.assertIn('John 14:6', driver.page_source)

        # Test clicking 'Start learning' for learn queue
        driver.find_element_by_css_selector('input[name=learnqueue]').click()
        self.wait_until_loaded('body')
        self.assertTrue(driver.current_url.endswith(reverse('learn')))

        self.wait_for_ajax()
        self.assertEqual(u"John 3:16", driver.find_element_by_id('id-verse-title').text)

        # Learn one verse (otherwise we are back to dashboard redirecting us)
        i.record_verse_action('John 3:16', 'NET', StageType.TEST, accuracy=1.0)

        # Test clicking 'Clear queue'
        driver.get(self.live_server_url + reverse('start'))
        driver.find_element_by_css_selector('input[name=clearqueue]').click()
        alert = driver.switch_to_alert()
        alert.accept()
        self.wait_until_loaded('body')

        # Since we cleared the queue, shouldn't have John 14:6 now
        self.assertTrue(driver.current_url.endswith(reverse('start')))
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
        driver.get(self.live_server_url + reverse('start'))
        self.assertIn('Psalm 23', driver.page_source)

        # Test 'Continue learning' button
        driver.find_element_by_id('id-learnpassage-btn-%d' % vs.id).click()
        self.wait_until_loaded('body')
        self.assertTrue(driver.current_url.endswith(reverse('learn')))
        self.wait_for_ajax()
        self.assertEqual(u"Psalm 23:1", driver.find_element_by_id('id-verse-title').text)

        # Test 'Cancel learning' button
        driver.get(self.live_server_url + reverse('start'))
        driver.find_element_by_id('id-cancelpassage-btn-%d' % vs.id).click()
        alert = driver.switch_to_alert()
        alert.accept()
        self.wait_until_loaded('body')
        self.assertNotIn('Psalm 23', driver.page_source)

    def test_home_dashboard_routing(self):
        driver = self.driver
        driver.get(self.live_server_url + "/")
        e = driver.find_element_by_css_selector('a.btn.large')
        self.assertTrue(e.get_attribute('href').endswith(reverse('start')))
        e.click()
        self.assertTrue(driver.current_url.endswith(reverse('choose')))
        self.assertEqual(Identity.objects.count(), 0)

