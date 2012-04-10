from __future__ import absolute_import

from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from paypal.standard.ipn.models import PayPalIPN

from .base import AccountTestMixin
from accounts.models import SubscriptionType, Account
from payments.hooks import paypal_payment_received
from payments.models import Price
from payments.sign import sign_payment_info

class IpnMock(object):
    pass


class PaymentTests(AccountTestMixin, TestCase):

    fixtures = ['test_bible_versions.json', 'test_currencies.json', 'test_prices.json']

    def setUp(self):
        super(PaymentTests, self).setUp()

        self.identity, self.account = self.create_account()

        # To stop tests from breaking in future, we update dates
        Price.objects.update(valid_until=timezone.now() + timedelta(10))

    def test_send_bad_payment_1(self):
        """
        Wrong format in 'custom'
        """
        price = Price.objects.get(description="One year", currency__name="GBP")

        ipn_1 = IpnMock()
        ipn_1.id = 123
        ipn_1.mc_gross = price.amount
        ipn_1.mc_currency = price.currency.name
        ipn_1.custom = "x" # wrong format

        self.assertEqual(len(mail.outbox), 0)
        paypal_payment_received(ipn_1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('/admin/ipn/paypal' in mail.outbox[0].body)

    def test_send_bad_payment_2(self):
        """
        Bad signature
        """
        price = Price.objects.get(description="One year", currency__name="GBP")

        ipn_1 = IpnMock()
        ipn_1.id = 123
        ipn_1.mc_gross = price.amount
        ipn_1.mc_currency = price.currency.name
        ipn_1.custom = sign_payment_info(dict(account=self.account.id, price=price.id)) + "xxx"

        self.assertEqual(len(mail.outbox), 0)
        paypal_payment_received(ipn_1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('/admin/ipn/paypal' in mail.outbox[0].body)

    def test_send_bad_payment_3(self):
        """
        Outside 'valid_until'
        """
        Price.objects.update(valid_until=timezone.now() - timedelta(10))
        price = Price.objects.get(description="One year", currency__name="GBP")

        ipn_1 = IpnMock()
        ipn_1.id = 123
        ipn_1.mc_gross = price.amount
        ipn_1.mc_currency = price.currency.name
        ipn_1.custom = sign_payment_info(dict(account=self.account.id, price=price.id))

        self.assertEqual(len(mail.outbox), 0)
        paypal_payment_received(ipn_1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('/admin/ipn/paypal' in mail.outbox[0].body)

    def test_send_good_payment(self):
        price = Price.objects.get(description="One year", currency__name="GBP")
        self.account.date_joined = timezone.now() - timedelta(1000)
        self.account.save()

        ipn_1 = PayPalIPN.objects.create(mc_gross=price.amount,
                                         mc_currency=price.currency.name,
                                         custom=sign_payment_info(dict(account=self.account.id,
                                                                       price=price.id)),
                                         ipaddress="127.0.0.1",
                                         )

        self.assertEqual(len(mail.outbox), 0)
        paypal_payment_received(ipn_1)
        self.account = Account.objects.get(id=self.account.id)
        self.assertEqual(self.account.payments.count(), 1)
        self.assertEqual(self.account.subscription, SubscriptionType.PAID_UP)
        self.assertTrue(self.account.paid_until is not None)

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('Your account is now paid up' in mail.outbox[0].body)

    def test_send_good_payment_when_paid_up_and_payment_possible(self):
        price = Price.objects.get(description="One year", currency__name="GBP")
        self.account.date_joined = timezone.now() - timedelta(1000)
        self.account.save()
        # Need to use update() for paid_until and subscription
        Account.objects.filter(id=self.account.id).update(
            paid_until = timezone.now() + timedelta(2),
            subscription = SubscriptionType.PAID_UP,
            )
        self.account = Account.objects.get(id=self.account.id)

        ipn_1 = PayPalIPN.objects.create(mc_gross=price.amount,
                                         mc_currency=price.currency.name,
                                         custom=sign_payment_info(dict(account=self.account.id,
                                                                       price=price.id)),
                                         ipaddress="127.0.0.1",
                                         )

        self.assertEqual(len(mail.outbox), 0)
        paypal_payment_received(ipn_1)
        self.account = Account.objects.get(id=self.account.id)
        self.assertEqual(self.account.payments.count(), 1)

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('Your account is now paid up' in mail.outbox[0].body)

    def test_send_good_payment_when_paid_up_and_payment_not_possible(self):
        """
        Tests that payment is not saved but not acted upon if they are already
        paid up and before payment is allowed.
        """
        price = Price.objects.get(description="One year", currency__name="GBP")
        self.account.date_joined = timezone.now() - timedelta(1000)
        self.account.save()
        # Need to use update() for paid_until and subscription
        Account.objects.filter(id=self.account.id).update(
            paid_until = timezone.now() + timedelta(1000),
            subscription = SubscriptionType.PAID_UP,
            )
        self.account = Account.objects.get(id=self.account.id)


        ipn_1 = PayPalIPN.objects.create(mc_gross=price.amount,
                                         mc_currency=price.currency.name,
                                         custom=sign_payment_info(dict(account=self.account.id,
                                                                       price=price.id)),
                                         ipaddress="127.0.0.1",
                                         )

        self.assertEqual(len(mail.outbox), 0)
        paypal_payment_received(ipn_1)
        self.account = Account.objects.get(id=self.account.id)
        self.assertEqual(self.account.payments.count(), 1)

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('account is already paid up' in mail.outbox[0].body)
