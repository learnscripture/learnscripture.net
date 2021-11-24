from accounts.models import Account
from awards.models import AwardType
from bibleverses.models import VerseSet
from events.models import Event, EventType

from .base import FullBrowserTest
from .test_bibleverses import RequireExampleVerseSetsMixin


class ReferralsTests(RequireExampleVerseSetsMixin, FullBrowserTest):
    def test_register_referral(self):
        # NB: these are are not the identity we are going to use.
        identity, account = self.create_account()

        self.assertEqual(account.referred_identities_count(), 0)

        # Start at home page
        start_url = account.make_referral_link("/")
        self.get_literal_url(start_url)
        self.wait_until_loaded("body")
        self.click("a.btn.primary")

        # Should be at 'choose' page now
        vs = VerseSet.objects.get(slug="bible-101")
        self.click("#id-choose-verseset .accordion-heading")
        self.click("#id-learn-verseset-btn-%d" % vs.id)
        self.set_preferences()

        # Definitely have created new identity now, which should be linked to
        # the account that was referred from.

        # refresh account:
        account = Account.objects.get(id=account.id)

        self.assertEqual(account.referred_identities_count(), 1)

        new_account_event_count_1 = Event.objects.filter(event_type=EventType.NEW_ACCOUNT).count()

        # If they create an account, referree gets a badge
        self.get_url("dashboard")
        self.create_account_interactive()
        self.assertEqual(account.awards.filter(award_type=AwardType.RECRUITER).count(), 1)

        # Hack another test here - event should be recorded
        new_account_event_count_2 = Event.objects.filter(event_type=EventType.NEW_ACCOUNT).count()
        self.assertEqual(new_account_event_count_2 - new_account_event_count_1, 1)
