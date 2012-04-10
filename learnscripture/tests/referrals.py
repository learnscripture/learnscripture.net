from __future__ import absolute_import

from accounts.models import Account
from bibleverses.models import VerseSet

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
        driver.find_element_by_css_selector('a.btn.primary').click()

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

