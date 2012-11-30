from __future__ import absolute_import

from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone
from paypal.standard.ipn.models import PayPalIPN

from .base import AccountTestMixin
from accounts.models import Account
from payments.hooks import paypal_payment_received
from payments.models import Price, Currency
from payments.sign import sign_payment_info

class IpnMock(object):
    payment_status = 'Completed'


class PaymentTests(AccountTestMixin, TestCase):

    fixtures = ['test_bible_versions.json', 'test_currencies.json']

    def setUp(self):
        super(PaymentTests, self).setUp()

        self.identity, self.account = self.create_account()

    def test_send_bad_payment_1(self):
        """
        Wrong format in 'custom'
        """
        ipn_1 = IpnMock()
        ipn_1.id = 123
        ipn_1.mc_gross = Decimal("10.00")
        ipn_1.mc_currency = "GBP"
        ipn_1.custom = "x" # wrong format

        self.assertEqual(len(mail.outbox), 0)
        paypal_payment_received(ipn_1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('/admin/ipn/paypal' in mail.outbox[0].body)

    def test_send_bad_payment_2(self):
        """
        Bad signature
        """
        ipn_1 = IpnMock()
        ipn_1.id = 123
        ipn_1.mc_gross = Decimal("10.00")
        ipn_1.mc_currency = "GBP"
        ipn_1.custom = sign_payment_info(dict(account=self.account.id)) + "xxx"

        self.assertEqual(len(mail.outbox), 0)
        paypal_payment_received(ipn_1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('/admin/ipn/paypal' in mail.outbox[0].body)

    def test_send_good_payment(self):
        ipn_1 = PayPalIPN.objects.create(mc_gross=Decimal("10.00"),
                                         mc_currency="GBP",
                                         custom=sign_payment_info(dict(account=self.account.id)),
                                         ipaddress="127.0.0.1",
                                         payment_status='Completed',
                                         )

        self.assertEqual(len(mail.outbox), 0)
        paypal_payment_received(ipn_1)
        self.account = Account.objects.get(id=self.account.id)
        self.assertEqual(self.account.payments.count(), 1)

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('Thank you for your donation' in mail.outbox[0].body)


class PriceTests(AccountTestMixin, TestCase):

    fixtures = ['test_bible_versions.json', 'test_currencies.json', 'test_prices.json']

    def test_current_prices(self):
        prices_groups = Price.objects.current_prices(with_discount=Decimal('0.10'))
        self.assertEqual(
            [(currency.name, [(p.days, p.amount, p.amount_with_discount)
                              for p in prices])
             for currency, prices in prices_groups],
            [(u'GBP',
              [(93, Decimal('1.50'), Decimal('1.30')),
               (366, Decimal('5.00'), Decimal('4.50'))]),
             (u'USD',
              [(93, Decimal('2.50'), Decimal('2.20')),
               (366, Decimal('8.00'), Decimal('7.20'))])]
            )

