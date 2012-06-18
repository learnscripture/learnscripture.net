from __future__ import absolute_import

from datetime import timedelta
from decimal import Decimal

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from accounts.models import SubscriptionType, Account
from bibleverses.models import VerseSet
from payments.models import Currency
from .base import LiveServerTests

SUBSCRIPTION_NOT_DUE = "Your subscription is not due for renewal"

class SubscribeTests(LiveServerTests):

    fixtures = ['test_bible_versions.json',
                'test_bible_verses.json',
                'test_verse_sets.json',
                'test_currencies.json',
                'test_prices.json']

    def test_no_payment_allowed_until_close_to_end_of_free_trial(self):
        identity, account = self.create_account()
        self.login(account)
        driver = self.driver
        driver.get(self.live_server_url + reverse('subscribe'))
        self.assertIn(SUBSCRIPTION_NOT_DUE, driver.page_source)

    def test_no_payment_allowed_until_close_to_end_of_paid_period(self):
        identity, account = self.create_account()

        Account.objects.filter(id=account.id).update(
            subscription=SubscriptionType.PAID_UP,
            # 100 > PAYMENT_ALLOWED_EARLY_DAYS
            paid_until=timezone.now() + timedelta(100),
            )

        self.login(account)
        driver = self.driver
        driver.get(self.live_server_url + reverse('subscribe'))
        self.assertIn(SUBSCRIPTION_NOT_DUE, driver.page_source)

    def test_payment_allowed_if_close_to_end_of_free_trial(self):
        identity, account = self.create_account()
        # (FREE_TRIAL_LENGTH_DAYS - PAYMENT_ALLOWED_EARLY_DAYS) < 50 < FREE_TRIAL_LENGTH_DAYS
        account.date_joined = timezone.now() - timedelta(50)
        account.save()

        self.login(account)
        driver = self.driver
        driver.get(self.live_server_url + reverse('subscribe'))
        self.assertNotIn(SUBSCRIPTION_NOT_DUE, driver.page_source)

    def test_payment_required_if_overdue(self):
        identity, account = self.create_account()
        # 100 > FREE_TRIAL_LENGTH_DAYS
        account.date_joined = timezone.now() - timedelta(100)
        account.save()
        self.login(account)

        # Add some verses.
        vs1 = VerseSet.objects.get(name='Bible 101')
        identity.add_verse_set(vs1)
        identity.verse_statuses.filter(reference='John 3:16').update(
            strength=0.7, last_tested=timezone.now())
        identity.verse_statuses.filter(reference='John 14:6').update(
            strength=0.75, last_tested=timezone.now())

        driver = self.driver
        # Check for redirect
        driver.get(self.live_server_url + reverse('dashboard'))
        self.wait_until_loaded('body')
        self.assertTrue(driver.current_url.endswith(reverse('subscribe')))

        # Check for text saying 'you've learned....'
        self.assertIn(u'You could probably recite John 3:16 and John 14:6 right now', driver.page_source)

    def test_payment_allowed_if_close_to_end_of_paid_period(self):
        identity, account = self.create_account()

        Account.objects.filter(id=account.id).update(
            subscription=SubscriptionType.PAID_UP,
            # 5 < PAYMENT_ALLOWED_EARLY_DAYS
            paid_until=timezone.now() + timedelta(5),
            )

        self.login(account)
        driver = self.driver
        driver.get(self.live_server_url + reverse('subscribe'))
        self.assertNotIn(SUBSCRIPTION_NOT_DUE, driver.page_source)

    def test_no_payment_allowed_if_lifetime_free(self):
        identity, account = self.create_account()
        Account.objects.filter(id=account.id).update(subscription=SubscriptionType.LIFETIME_FREE)
        self.login(account)
        driver = self.driver
        driver.get(self.live_server_url + reverse('subscribe'))
        self.assertIn(SUBSCRIPTION_NOT_DUE, driver.page_source)

    def test_downgrade(self):
        identity, account = self.create_account()
        account.date_joined = timezone.now() - timedelta(100)
        account.save()

        self.login(account)
        driver = self.driver
        driver.get(self.live_server_url + reverse('subscribe'))

        driver.find_element_by_css_selector('#id_currency_0').click()
        driver.find_element_by_css_selector('#id_price_GBP_cant_afford').click()
        driver.find_element_by_css_selector('input[name=downgrade]').click()

        account = Account.objects.get(id=account.id)
        self.assertEqual(account.subscription, SubscriptionType.BASIC)

    def test_upgrade(self):
        identity, account = self.create_account()
        Account.objects.filter(id=account.id).update(
            subscription=SubscriptionType.BASIC,
            )

        self.login(account)
        driver = self.driver
        driver.get(self.live_server_url + reverse('subscribe'))
        self.assertNotIn(SUBSCRIPTION_NOT_DUE, driver.page_source)
        driver.find_element_by_css_selector('#id_currency_0').click()
        driver.find_element_by_css_selector('#id_price_GBP_3').click()

    def test_pay_from_fund(self):
        identity, account = self.create_account()

        # Add some verses, to stop redirect to 'choose' page
        vs1 = VerseSet.objects.get(name='Bible 101')
        identity.add_verse_set(vs1)

        # Create the fund
        currency = Currency.objects.get(name='GBP')
        fund = account.funds_managed.create(name='church',
                                            currency=currency,
                                            balance=Decimal('6.00'),
                                            )
        fund.members.add(account)

        # Payment overdue:
        # 100 > FREE_TRIAL_LENGTH_DAYS
        account.date_joined = timezone.now() - timedelta(100)
        account.save()
        self.login(account)

        driver = self.driver
        driver.get(self.live_server_url + reverse('dashboard'))
        self.wait_until_loaded('body')
        self.assertTrue(driver.current_url.endswith(reverse('subscribe')))

        self.assertIn("you can use that fund", driver.page_source)

        driver.find_element_by_css_selector("[name=usefund]").click()
        self.wait_until_loaded('body')
        self.assertTrue(driver.current_url.endswith(reverse('dashboard')))

