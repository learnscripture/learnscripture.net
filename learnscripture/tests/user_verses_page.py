from __future__ import absolute_import

from datetime import timedelta

from django.core.urlresolvers import reverse
from django.utils import timezone

from bibleverses.models import VerseSet, MemoryStage
from .base import LiveServerTests


class UserVersesPageTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def test_practice_button(self):
        identity, account = self.create_account()

        # Add a passage
        vs = VerseSet.objects.get(slug='psalm-23')
        vs.breaks = "23:4"
        vs.save()
        identity.add_verse_set(vs)

        # Make 'tested', but not needing revision
        identity.verse_statuses.update(strength=0.5,
                                       last_tested=timezone.now() - timedelta(days=10),
                                       next_test_due=timezone.now() + timedelta(days=1),
                                       memory_stage=MemoryStage.TESTED)

        self.login(account)

        driver = self.driver
        driver.get(self.live_server_url + reverse('user_verses'))
        self.wait_until_loaded('body')

        for i in range(1, 7):
            self.assertIn("Psalm 23:%d" % i, driver.page_source)

        driver.find_element_by_css_selector('a.btn[data-reference="Psalm 23:2"]').click()
        self.wait_for_ajax()

        # 'Practise verse' button
        btn1 = driver.find_element_by_css_selector('input[name="reviseverse"]')
        self.assertEqual(btn1.get_attribute('value'), "Practise verse")

        # 'Practise section' button
        btn2 = driver.find_element_by_css_selector('input[name="practisepassagesection"]')
        self.assertEqual(btn2.get_attribute('value'), "Practise section: Psalm 23:1-3")

        # 'Practise passage' button
        btn3 = driver.find_element_by_css_selector('input[name="practisepassage"]')
        self.assertEqual(btn3.get_attribute('value'), "Practise passage: Psalm 23:1-6")

        # Click "practise section":
        btn2.click()
        self.wait_until_loaded('body')
        self.wait_for_ajax()

        self.assertTrue(driver.current_url.endswith(reverse('learn')))
        self.assertIn("Psalm 23:1", driver.page_source)

        # Should be in 'practise' mode
        self.assertTrue(driver.find_element_by_css_selector(".instructions-practice").is_displayed())
