from __future__ import absolute_import

from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from paypal.standard.ipn.models import PayPalIPN

from .base import AccountTestMixin
from accounts.models import Account
from payments.hooks import paypal_payment_received
from payments.models import DonationDrive
from payments.sign import sign_payment_info

__all__ = ['PaymentTests', 'DonationDriveTests']


class IpnMock(object):
    payment_status = 'Completed'


def good_payment_ipn(account, amount):
    return PayPalIPN.objects.create(mc_gross=amount,
                                    mc_currency="GBP",
                                    custom=sign_payment_info(dict(account=account.id)),
                                    ipaddress="127.0.0.1",
                                    payment_status='Completed',
                                    )


class PaymentTests(AccountTestMixin, TestCase):

    fixtures = ['test_bible_versions.json']

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
        ipn_1 = good_payment_ipn(self.account, Decimal("10.00"))
        self.assertEqual(len(mail.outbox), 0)
        paypal_payment_received(ipn_1)
        self.account = Account.objects.get(id=self.account.id)
        self.assertEqual(self.account.payments.count(), 1)

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('Thank you for your donation' in mail.outbox[0].body)


class DonationDriveTests(AccountTestMixin, TestCase):

    fixtures = ['test_bible_versions.json']

    def setUp(self):
        super(DonationDriveTests, self).setUp()
        self.identity, self.account = self.create_account()

    def test_donation_drive_active(self):
        d = DonationDrive.objects.create(
            start=timezone.now() - timedelta(days=10),
            finish=timezone.now() + timedelta(days=10),
            active=True,
            message_html="Please donate!",
            hide_if_donated_days=4,
            )
        d2 = DonationDrive.objects.current()[0]
        self.assertEqual(d2, d)
        self.assertEqual(d2.active_for_account(self.account),
                         True)

        # Now make payment
        ipn_1 = good_payment_ipn(self.account, Decimal("1.00"))
        paypal_payment_received(ipn_1)

        # No longer active
        self.assertEqual(d2.active_for_account(self.account),
                         False)


        # Now move payments into past
        self.account.payments.update(created=timezone.now() - timedelta(days=5))

        # Should be active again
        self.assertEqual(d2.active_for_account(self.account),
                         True)
