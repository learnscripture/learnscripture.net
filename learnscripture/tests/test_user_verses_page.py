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
        self.get_url('user_verses')

        for i in range(1, 7):
            self.assertIn("Psalm 23:%d" % i, driver.page_source)

        self.click('a.btn[data-reference="Psalm 23:2"]')

        # 'Practise verse' button
        btn1 = self.find('input[name="reviseverse"]')
        self.assertEqual(btn1.get_attribute('value'), "Practise verse")

        # 'Practise section' button
        btn2 = self.find('input[name="practisepassagesection"]')
        self.assertEqual(btn2.get_attribute('value'), "Practise section: Psalm 23:1-3")

        # 'Practise passage' button
        btn3 = self.find('input[name="practisepassage"]')
        self.assertEqual(btn3.get_attribute('value'), "Practise passage: Psalm 23:1-6")

        # Click "practise section":
        self.click(btn2)

        self.assertTrue(driver.current_url.endswith(reverse('learn')))
        self.assertIn("Psalm 23:1", driver.page_source)

        # Should be in 'practise' mode
        self.assertTrue(self.find("#id-instructions .stage-practice").is_displayed())

        # Type the verse:
        words = "The LORD is my shepherd I shall not want"
        for word in words.split():
            self.send_keys("#id-typing", word + " ")

        # Click finish
        self.click("#id-finish-btn")

        # Should have gone back to where we came from
        self.assertTrue(driver.current_url.endswith(reverse('user_verses')))
