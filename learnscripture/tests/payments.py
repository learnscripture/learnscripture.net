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
from payments.models import Price, Currency, Fund
from payments.sign import sign_payment_info

class IpnMock(object):
    payment_status = 'Completed'


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
        ipn_1.custom = sign_payment_info(dict(account=self.account.id,
                                              price=price.id,
                                              amount=str(price.amount))) + "xxx"

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
        ipn_1.custom = sign_payment_info(dict(account=self.account.id,
                                              price=price.id,
                                              amount=str(price.amount)))

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
                                                                       price=price.id,
                                                                       amount=str(price.amount),
                                                                       )),
                                         ipaddress="127.0.0.1",
                                         payment_status='Completed',
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
                                                                       price=price.id,
                                                                       amount=str(price.amount))),
                                         ipaddress="127.0.0.1",
                                         payment_status='Completed',
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
                                                                       price=price.id,
                                                                       amount=str(price.amount))),
                                         ipaddress="127.0.0.1",
                                         payment_status='Completed',
                                         )

        self.assertEqual(len(mail.outbox), 0)
        paypal_payment_received(ipn_1)
        self.account = Account.objects.get(id=self.account.id)
        self.assertEqual(self.account.payments.count(), 1)

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('account is already paid up' in mail.outbox[0].body)

    def test_add_to_payment_fund(self):
        currency = Currency.objects.get(name='GBP')
        fund = self.account.funds_managed.create(name='my church',
                                                 currency=currency)
        ipn_1 = PayPalIPN.objects.create(mc_gross=Decimal('20.00'),
                                         mc_currency=currency.name,
                                         custom=sign_payment_info(dict(fund=fund.id,
                                                                       currency=fund.currency.name)),
                                         ipaddress="127.0.0.1",
                                         payment_status='Completed',
                                         )

        self.assertEqual(len(mail.outbox), 0)

        paypal_payment_received(ipn_1)

        # refresh
        fund = Fund.objects.get(id=fund.id)
        # Check payments
        self.assertEqual(fund.payments.count(), 1)
        self.assertEqual(fund.balance, Decimal('20.00'))
        # Check emails
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Thank you for your payment', mail.outbox[0].body)
        self.assertIn(fund.name, mail.outbox[0].body)
        self.assertIn('20.00', mail.outbox[0].body)


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


class FundTests(AccountTestMixin, TestCase):

    fixtures = ['test_bible_versions.json', 'test_currencies.json', 'test_prices.json']

    def test_pay_for(self):
        identity, account = self.create_account()
        account.date_joined = timezone.now() - timedelta(1000)
        account.save()

        self.assertTrue(account.payment_possible())

        currency = Currency.objects.get(name='GBP')
        fund = account.funds_managed.create(name='church',
                                            currency=currency,
                                            balance=Decimal('6.00'))

        # Can't pay for account if account is not a member
        self.assertFalse(fund.can_pay_for(account))

        fund.members.add(account)
        self.assertTrue(fund.can_pay_for(account))

        # Test 'pay_for' updates account.paid_until
        fund.pay_for(account)

        # refresh
        fund = Fund.objects.get(id=fund.id)
        account = Account.objects.get(id=account.id)

        self.assertEqual(fund.balance, Decimal('1.00'))
        self.assertFalse(account.payment_possible())

        # Can't pay if we're out of funds.
        self.assertFalse(fund.can_pay_for(account))

