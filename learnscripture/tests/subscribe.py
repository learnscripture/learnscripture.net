from __future__ import absolute_import

from datetime import timedelta

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from accounts.models import SubscriptionType, Account
from .base import LiveServerTests

SUBSCRIPTION_NOT_DUE = "Your subscription is not due for renewal"

class SubscribeTests(LiveServerTests):

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

