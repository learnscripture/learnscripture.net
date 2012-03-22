from __future__ import absolute_import

from datetime import timedelta

from django.db.models import F
from django.test import TestCase
from django.core import mail

from accounts.models import Account
from accounts.email_reminders import send_email_reminders
from bibleverses.models import VerseSet, StageType

from .base import AccountTestMixin

class EmailReminderTests(AccountTestMixin, TestCase):

    fixtures = ['test_bible_versions.json', 'test_verse_sets.json', 'test_bible_verses.json']

    def test_send(self):
        identity, account = self.create_account()
        account.remind_after = 2
        account.remind_every = 3
        account.save()

        # First create something that would need an email reminder
        vs1 = VerseSet.objects.get(name='Bible 101')
        identity.add_verse_set(vs1)

        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1)

        # It is easier to move dates in DB back to simulate the progress of
        # time.
        def move_back(days):
            identity.verse_statuses.update(
                next_test_due=F('next_test_due') - timedelta(days)
                )
            a = Account.objects.get(id=account.id)
            if a.last_reminder_sent is not None:
                a.last_reminder_sent -= timedelta(days)
                a.save()

        self.assertEqual(mail.outbox, [])

        # Shouldn't get reminder after 1 day
        move_back(1.0)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 0)

        # Should get reminder after 2.1 days
        move_back(1.1)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 1)

        # Shouldn't get another if we run script again
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 1)

        # Shouldn't get another after 3.1 days
        move_back(1.0)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 1)

        # Shouldn't get another after 4.1 days
        move_back(1.0)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 1)

        # Should get another after 5.2 days
        move_back(1.1)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 2)
