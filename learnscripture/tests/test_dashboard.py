from __future__ import absolute_import

from datetime import timedelta

from django.core.urlresolvers import reverse
from django.db.models import F
from django.utils import timezone

import accounts.memorymodel
from accounts.models import Identity, Notice
from bibleverses.models import VerseSet, TextVersion, StageType, MemoryStage

from .base import FullBrowserTest


class DashboardTests(FullBrowserTest):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json',
                'test_catechisms.json']

    def test_redirect(self):
        self.get_url('dashboard')
        self.assertUrlsEqual(reverse('login'))

    def _assert_learning_reference(self, ref):
        self.assertUrlsEqual(reverse('learn'))
        self.assertEqual(ref, self.find("#id-verse-title").text)

    def _click_clear_learning_queue_btn(self, verse_set_id):
        # Avoid 'self.click' which is buggy when alerts are produced
        self.find('#id-learning-queue-verse-set-%s input[name=clearbiblequeue]' % (verse_set_id if verse_set_id else '')).click()
        self.confirm()

    def test_learn_queue(self):
        # This combines a bunch of tests, it's easier to avoid a lot of
        # repetition that way.
        i = self.setup_identity()

        # Add a verse set
        vs = VerseSet.objects.get(slug='bible-101')
        i.add_verse_set(vs)

        # And an individual verse
        i.add_verse_choice('Psalm 23:2')

        # Test verses appear on dashboard
        self.get_url('dashboard')
        self.assertTextPresent('John 3:16')
        self.assertTextPresent('John 14:6')
        self.assertTextPresent('Psalm 23:2')

        # Test click 'Start learning' for 'Bible 101' verse set
        self.assertTextPresent('Bible 101')
        self.click('#id-learning-queue-verse-set-%s input[name=learnbiblequeue]' % vs.id)
        self._assert_learning_reference(u"John 3:16")

        # Learn one verse (otherwise we are back to dashboard redirecting us)
        i.record_verse_action('John 3:16', 'NET', StageType.TEST, accuracy=1.0)

        self.get_url('dashboard')
        # Test clicking 'Start learning' for general queue
        self.click('#id-learning-queue-verse-set- input[name=learnbiblequeue]')
        self._assert_learning_reference(u"Psalm 23:2")

        # Test clicking 'Clear queue'
        self.get_url('dashboard')
        self._click_clear_learning_queue_btn(vs.id)

        # Since we cleared the queue, shouldn't have John 14:6 now
        self.assertUrlsEqual(reverse('dashboard'))
        self.assertTextAbsent('John 14:6')

        # but should still have Psalm 23:2
        self.assertTextPresent('Psalm 23:2')

        # Click the other 'Clear queue' button
        self._click_clear_learning_queue_btn(None)

        self.assertTextAbsent('Psalm 23:2')

    def test_learn_passage(self):
        # As above, combine several tests as a story, for simplicity
        i = self.setup_identity()

        # This is to stop redirecting behaviour due to an empty dashboard
        i.add_verse_set(VerseSet.objects.get(slug='bible-101'))

        # Add a passage
        vs = VerseSet.objects.get(slug='psalm-23')
        i.add_verse_set(vs)

        # Test dashboard text
        self.get_url('dashboard')
        self.assertTextPresent('Psalm 23')

        # Test 'Continue learning' button
        self.submit('#id-learnpassage-btn-%d' % vs.id)
        self.assertUrlsEqual(reverse('learn'))
        self.assertEqual(u"Psalm 23:1", self.find("#id-verse-title").text)

        # Test 'Cancel learning' button
        self.get_url('dashboard')
        self.find('#id-cancelpassage-btn-%d' % vs.id).click()
        self.confirm()
        self.assertTextAbsent('Psalm 23')

    def test_learn_catechism(self):
        i = self.setup_identity()
        i.add_catechism(TextVersion.objects.get(slug='WSC'))
        self.get_url('dashboard')
        self.assertTextPresent("You've queued this catechism for learning, 4 questions total")

        self.click('input[name=learncatechismqueue]')
        self.assertUrlsEqual(reverse('learn'))
        self.assertEqual(u"Q1. What is the chief end of man?", self.find("#id-verse-title").text)

        i.record_verse_action('Q1', 'WSC', StageType.TEST, accuracy=1.0)

        # Test clicking 'Clear queue'
        self.get_url('dashboard')
        self.find('input[name=clearcatechismqueue]').click()
        self.confirm()

        # Since we cleared the queue, shouldn't have anything about catechisms now
        self.assertUrlsEqual(reverse('dashboard'))
        self.assertTextAbsent('catechism')

    def test_revise_one_section(self):
        i = self.setup_identity()

        # Add a passage
        vs = VerseSet.objects.get(slug='psalm-23')
        vs.breaks = "23:4"
        vs.save()
        i.add_verse_set(vs)

        # Get to 'group testing' stage
        i.verse_statuses.update(strength=accounts.memorymodel.STRENGTH_FOR_GROUP_TESTING + 0.01,
                                last_tested=timezone.now() - timedelta(days=10),
                                next_test_due=timezone.now() - timedelta(days=1),
                                memory_stage=MemoryStage.TESTED)

        self.get_url('dashboard')
        self.assertTextPresent('Psalm 23')  # sanity check

        self.click('input[value^="Review one section"][name=revisepassagenextsection]')
        self.assertTextPresent("Psalm 23:1")

        # Skip through
        def skip():
            self.click("#id-verse-dropdown")
            self.click(text="Skip this")
        skip()
        self.assertTextPresent("Psalm 23:2")
        skip()
        self.assertTextPresent("Psalm 23:3")
        skip()
        self.wait_until_loaded('body')

        # Should be back at dashboard
        self.assertUrlsEqual(reverse('dashboard'))

    def test_home_dashboard_routing(self):
        Identity.objects.all().delete()
        self.get_url('home')
        self.click('a.btn.large[href="{0}"]'.format(reverse('choose')))
        self.assertUrlsEqual(reverse('choose'))
        # Getting this far shouldn't create an Identity
        self.assertEqual(Identity.objects.count(), 0)

    def test_notices_expire(self):
        # This could be tested on any page, but this is an obvious example.
        identity, account = self.create_account()
        self.login(account)
        account.add_html_notice("Hello you crazy guy!")

        self.assertEqual(identity.notices.all()[0].seen, None)

        self.get_url('dashboard')
        self.assertTextPresent("Hello you crazy guy!")

        self.assertNotEqual(identity.notices.all()[0].seen, None)

        # Move database into 'past'
        Notice.objects.update(seen=F('seen') - timedelta(days=10))

        self.get_url('dashboard')
        self.assertTextAbsent("Hello you crazy guy!")
