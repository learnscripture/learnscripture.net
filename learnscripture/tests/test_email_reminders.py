import re
import urllib.parse
from datetime import datetime, timedelta

import mock
from django.core import mail
from django.db.models import F
from django.test.client import RequestFactory
from django.utils import timezone

import learnscripture.mail.views
from accounts.email_reminders import send_email_reminders
from accounts.models import Account
from bibleverses.models import StageType, VerseSet

from .base import AccountTestMixin, TestBase
from .mailgun_test_data import (MAILGUN_EXAMPLE_POST_DATA_FOR_BOUNCE_ENDPOINT,
                                MAILGUN_EXAMPLE_POST_DATA_FOR_BOUNCE_ENDPOINT_CONTENT_TYPE)
from .test_bibleverses import RequireExampleVerseSetsMixin


class EmailReminderTests(RequireExampleVerseSetsMixin, AccountTestMixin, TestBase):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def setUp(self):
        super(EmailReminderTests, self).setUp()

        identity, account = self.create_account()
        account.remind_after = 2
        account.remind_every = 3
        account.save()

        # First create something that would need an email reminder
        vs1 = VerseSet.objects.get(name='Bible 101')
        identity.add_verse_set(vs1)

        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1)
        self.identity, self.account = identity, account

    # It is easier to move dates in DB back to simulate the progress of
    # time.
    def move_back(self, days):
        self.identity.verse_statuses.update(
            next_test_due=F('next_test_due') - timedelta(days),
            last_tested=F('last_tested') - timedelta(days),
        )
        a = Account.objects.get(id=self.account.id)
        if a.last_reminder_sent is not None:
            a.last_reminder_sent -= timedelta(days)
            a.save()

    def test_send(self):
        self.assertEqual(mail.outbox, [])

        # Shouldn't get reminder after 1 day
        self.move_back(1.0)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 0)

        # Should get reminder after 2.1 days
        self.move_back(1.1)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 1)

        # Shouldn't get another if we run script again
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 1)

        # Shouldn't get another after 3.1 days
        self.move_back(1.0)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 1)

        # Shouldn't get another after 4.1 days
        self.move_back(1.0)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 1)

        # Should get another after 5.2 days
        self.move_back(1.1)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 2)

    def test_remind_never(self):
        self.account.remind_after = 0
        self.account.save()
        self.move_back(20)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 0)

    def test_dont_send_for_inactive_users(self):
        self.assertEqual(mail.outbox, [])
        self.move_back(181)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 0)

    def test_login_link(self):
        self.move_back(3)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        m = re.search(r"https://.*/account\S*", msg.body)
        self.assertNotEqual(m, None)
        link = m.group()
        u = urllib.parse.urlparse(link)
        urllib.parse.urlunparse(('', '', u.path, u.params, u.query, u.fragment))
        r1 = self.client.get(link, follow=True)
        self.assertContains(r1, "Personal information")


class ReminderBounceTests(AccountTestMixin, TestBase):

    def test_mailgun_bounce(self):
        self.create_account(email="someone@gmail.com")

        rf = RequestFactory()
        request = rf.post('/', data=MAILGUN_EXAMPLE_POST_DATA_FOR_BOUNCE_ENDPOINT,
                          content_type=MAILGUN_EXAMPLE_POST_DATA_FOR_BOUNCE_ENDPOINT_CONTENT_TYPE)
        response = learnscripture.mail.views.mailgun_bounce_notification(request)

        # Due to out of date timestamp, will fail
        self.assertEqual(response.status_code, 403)

        # So mock that out:
        with mock.patch('learnscripture.mail.views.check_mailgun_timestamp',
                        new=lambda request: True):
            response2 = learnscripture.mail.views.mailgun_bounce_notification(request)
        self.assertEqual(response2.status_code, 200)

        self.assertEqual(Account.objects.filter(email='someone@gmail.com',
                                                email_bounced__isnull=True).count(),
                         0)
        self.assertEqual(Account.objects.get(email='someone@gmail.com').email_bounced,
                         timezone.make_aware(datetime(2016, 8, 2, 0, 32, 39),
                                             timezone.utc))
