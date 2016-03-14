from __future__ import absolute_import

from datetime import timedelta

from django.core.urlresolvers import reverse
from django.utils import timezone

from bibleverses.models import VerseSet, MemoryStage
from .base import FullBrowserTest


class UserVersesPageTests(FullBrowserTest):

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
        self.get_url('user_verses')

        for i in range(1, 7):
            self.assertTextPresent("Psalm 23:%d" % i)

        self.click('a.btn[data-reference="Psalm 23:2"]')

        # 'Practise verse' button
        self.assertEqual(self.get_element_attribute('input[name="reviseverse"]', 'value'),
                         "Practise verse")

        # 'Practise section' button
        self.assertEqual(self.get_element_attribute('input[name="practisepassagesection"]', 'value'),
                         "Practise section: Psalm 23:1-3")

        # 'Practise passage' button
        self.assertEqual(self.get_element_attribute('input[name="practisepassage"]', 'value'),
                         "Practise passage: Psalm 23:1-6")

        self.submit('input[name="practisepassagesection"]')

        self.assertUrlsEqual(reverse('learn'))
        self.assertTextPresent("Psalm 23:1")

        # Should be in 'practise' mode
        self.assertTrue(self.is_element_displayed("#id-instructions .stage-practice"))

        # Type the verse:
        words = "The LORD is my shepherd I shall not want"
        for word in words.split():
            self.fill({"#id-typing": word + " "})

        # Click finish
        self.submit("#id-finish-btn")

        # Should have gone back to where we came from
        self.assertUrlsEqual(reverse('user_verses'))
