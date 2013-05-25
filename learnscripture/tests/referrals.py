from __future__ import absolute_import

from accounts.models import Account
from awards.models import AwardType
from bibleverses.models import VerseSet
from events.models import Event, EventType

from .base import LiveServerTests


class ReferralsTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def test_register_referral(self):
        # NB: these are are not the identity we are going to use.
        identity, account = self.create_account()

        self.assertEqual(account.referred_identities_count(), 0)

        driver = self.driver
        # Start at home page
        start_url = account.make_referral_link(self.live_server_url)
        driver.get(start_url)
        self.find('a.btn.primary').click()

        # Should be at 'choose' page now
        vs = VerseSet.objects.get(slug='bible-101')
        driver.find_element_by_id("id-learn-verseset-btn-%d" % vs.id).click()
        self.set_preferences()
        self.wait_until_loaded('body')

        # Definitely have created new identity now, which should be linked to
        # the account that was referred from.

        # refresh account:
        account = Account.objects.get(id=account.id)

        self.assertEqual(account.referred_identities_count(), 1)


        new_account_event_count_1 = Event.objects.filter(event_type=EventType.NEW_ACCOUNT).count()

        # If they create an account, referree gets a badge
        self.create_account_interactive()
        self.assertEqual(account.awards.filter(award_type=AwardType.RECRUITER).count(), 1)

        # Hack another test here - event should be recorded
        new_account_event_count_2 = Event.objects.filter(event_type=EventType.NEW_ACCOUNT).count()
        self.assertEqual(new_account_event_count_2 - new_account_event_count_1, 1)
