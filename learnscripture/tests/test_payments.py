# -*- coding: utf-8 -*-

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core import mail
from django.utils import timezone
from paypal.standard.ipn.models import PayPalIPN

from accounts.models import Account
from payments.hooks import paypal_payment_received
from payments.models import DonationDrive
from payments.sign import sign_payment_info
from payments.signals import donation_drive_contributed_to, target_reached

from .base import AccountTestMixin, TestBase, WebTestBase


class IpnMock(object):
    payment_status = 'Completed'


def good_payment_ipn(account, amount, **kwargs):
    obj_args = dict(mc_gross=amount,
                    mc_currency="GBP",
                    custom=sign_payment_info(dict(account=account.id)),
                    ipaddress="127.0.0.1",
                    payment_status='Completed',
                    receiver_email=settings.PAYPAL_RECEIVER_EMAIL,
                    )
    obj_args.update(kwargs)
    return PayPalIPN.objects.create(**obj_args)


class PaymentTests(AccountTestMixin, TestBase):

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
        ipn_1.custom = "x"  # wrong format

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
        self.assertIn('Thank you for your donation', mail.outbox[0].body)
        self.assertIn('£10', mail.outbox[0].body)

    def test_USD_payment(self):
        ipn_1 = good_payment_ipn(self.account, Decimal("10.00"),
                                 mc_currency='USD',
                                 settle_currency='GBP',
                                 settle_amount=Decimal('6.50'))
        paypal_payment_received(ipn_1)
        self.account = Account.objects.get(id=self.account.id)
        self.assertEqual(self.account.payments.count(), 1)
        self.assertEqual(self.account.payments.all()[0].amount, Decimal('6.50'))


class DonationDriveTests(AccountTestMixin, TestBase):

    fixtures = ['test_bible_versions.json']

    def setUp(self):
        super(DonationDriveTests, self).setUp()
        self.identity, self.account = self.create_account()

    def test_donation_drive_active_for_account(self):
        d = DonationDrive.objects.create(
            start=timezone.now() - timedelta(days=10),
            finish=timezone.now() + timedelta(days=10),
            active=True,
            message_html="Please donate!",
            language_code="en",
            hide_if_donated_days=4,
        )

        d2 = DonationDrive.objects.current("en")[0]
        self.assertEqual(d2, d)
        self.assertEqual(d2.active_for_account(self.account),
                         False)  # because it is a recently created account

        self.account.date_joined -= timedelta(days=100)
        self.account.save()
        self.assertEqual(d2.active_for_account(self.account),
                         True)

        # Now make payment
        ipn_1 = good_payment_ipn(self.account, Decimal("1.00"))
        paypal_payment_received(ipn_1)

        # No longer active
        self.assertEqual(d2.active_for_account(self.account),
                         False)

        self.move_clock_on(timedelta(days=5))

        # Should be active again
        self.assertEqual(d2.active_for_account(self.account),
                         True)

        # Change language:
        self.account.is_tester = True  # For i18n_options_enabled
        self.account.identity.interface_language = "tr"
        self.assertEqual(d2.active_for_account(self.account),
                         False)

    def test_target(self):
        DonationDrive.objects.create(
            start=timezone.now() - timedelta(days=10),
            finish=timezone.now() + timedelta(days=10),
            active=True,
            message_html="Please donate!",
            language_code="en",
            hide_if_donated_days=4,
            target=Decimal("100")
        )
        current1 = DonationDrive.objects.current("en")
        self.assertEqual(len(current1), 1)

        d1 = current1[0]
        self.assertEqual(d1.fraction_raised, 0)

        # Make a payment
        ipn_1 = good_payment_ipn(self.account, Decimal("20.00"))
        paypal_payment_received(ipn_1)

        current2 = DonationDrive.objects.current("en")
        d2 = current2[0]
        self.assertEqual(d2.fraction_raised, Decimal('0.2'))

        # Another payment, taking beyond target
        ipn_2 = good_payment_ipn(self.account, Decimal("90.00"))
        paypal_payment_received(ipn_2)

        current3 = DonationDrive.objects.current("en")
        self.assertEqual(len(current3), 0)

    def test_target_reached_signal(self):
        # Test whether the donation_drive_contributed_to and target_reached fire
        # at the right times.

        DonationDrive.objects.create(
            start=timezone.now() - timedelta(days=10),
            finish=timezone.now() + timedelta(days=10),
            active=True,
            message_html="Please donate!",
            hide_if_donated_days=4,
            target=Decimal("20")
        )

        self.donation_drive_contributed_to_called = 0
        self.target_reached_called = 0

        def donation_drive_contributed_to_handler(sender, **kwargs):
            self.donation_drive_contributed_to_called += 1
            self.assertEqual(sender, DonationDrive.objects.get())

        def target_reached_handler(sender, **kwargs):
            self.target_reached_called += 1
            self.assertEqual(sender, DonationDrive.objects.get())

        donation_drive_contributed_to.connect(donation_drive_contributed_to_handler)
        target_reached.connect(target_reached_handler)

        # Make a payment
        ipn_1 = good_payment_ipn(self.account, Decimal("15.00"))
        paypal_payment_received(ipn_1)

        self.assertEqual(self.donation_drive_contributed_to_called, 1)
        self.assertEqual(self.target_reached_called, 0)

        # Make another payment, taking up to target
        ipn_2 = good_payment_ipn(self.account, Decimal("5.00"))
        paypal_payment_received(ipn_2)

        self.assertEqual(self.donation_drive_contributed_to_called, 2)
        self.assertEqual(self.target_reached_called, 1)

        # Make another payment, taking past target
        ipn_3 = good_payment_ipn(self.account, Decimal("5.00"))
        paypal_payment_received(ipn_3)

        self.assertEqual(self.donation_drive_contributed_to_called, 3)
        # Should only have been called the once
        self.assertEqual(self.target_reached_called, 1)

    def test_target_reached_emails(self):
        # Check that we send out emails to donors when a target is reached.
        DonationDrive.objects.create(
            start=timezone.now() - timedelta(days=10),
            finish=timezone.now() + timedelta(days=10),
            active=True,
            message_html="Please donate!",
            hide_if_donated_days=4,
            target=Decimal("20")
        )
        ipn_1 = good_payment_ipn(self.account, Decimal("10.00"))
        paypal_payment_received(ipn_1)

        i, account2 = self.create_account(username="test")

        ipn_2 = good_payment_ipn(account2, Decimal("10.00"))
        paypal_payment_received(ipn_2)

        mails = [m for m in mail.outbox
                 if m.subject == "LearnScripture.net - donation target reached!" and
                 m.to != [e for n, e in settings.ADMINS]]

        self.assertEqual(len(mails), 2)
        self.assertIn("Our target of £20.00 was reached", mails[0].body)
        self.assertIn("Thanks to your contribution of £10.00 we reached our funding target.\n\n", mails[0].body)


class ViewDonationDriveTests(WebTestBase):
    def setUp(self):
        super(ViewDonationDriveTests, self).setUp()
        self.donation_drive = DonationDrive.objects.create(
            start=timezone.now() - timedelta(days=10),
            finish=timezone.now() + timedelta(days=10),
            active=True,
            message_html="Please donate!",
            language_code="en",
            hide_if_donated_days=4,
            target=Decimal("20")
        )
        self.identity, self.account = self.create_account()
        self.account.date_joined -= timedelta(days=100)
        self.account.save()

    def test_view(self):
        self.login(self.account)
        self.get_url("dashboard")
        self.assertTextPresent("Please donate!")
