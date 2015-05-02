from __future__ import absolute_import

from datetime import timedelta, datetime
import re
import urlparse
import StringIO

from django.db.models import F
from django.test import TestCase
from django.core import mail
from django.utils import timezone

from accounts.models import Account
from accounts.email_reminders import send_email_reminders, handle_bounce
from bibleverses.models import VerseSet, StageType

from .base import AccountTestMixin

__all__ = ['EmailReminderTests']


class EmailReminderTests(AccountTestMixin, TestCase):

    fixtures = ['test_bible_versions.json', 'test_verse_sets.json', 'test_bible_verses.json']

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
            next_test_due=F('next_test_due') - timedelta(days)
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

    def test_login_link(self):
        self.move_back(3)
        send_email_reminders()
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        m = re.search("http://.*/account\S*", msg.body)
        self.assertNotEqual(m, None)
        link = m.group()
        u = urlparse.urlparse(link)
        urlparse.urlunparse(('', '', u.path, u.params, u.query, u.fragment))
        r1 = self.client.get(link, follow=True)
        self.assertContains(r1, "Send first reminder")


class ReminderBounceTests(AccountTestMixin, TestCase):

    def test_email_1(self):
        self.create_account(email="someone@gmail.com")
        bounce_email = """Return-Path: <>
Received: from mx9.webfaction.com ([127.0.0.1])
	by localhost (mail9.webfaction.com [127.0.0.1]) (amavisd-new, port 10024)
	with ESMTP id wzY5CR9li+OB for <anon@somewhere.net>;
	Tue, 28 Apr 2015 01:01:36 +0000 (UTC)
Received: from smtp.webfaction.com (smtp.webfaction.com [74.55.86.74])
	by mx9.webfaction.com (Postfix) with ESMTP id 123E61A388AD4
	for <website@learnscripture.net>; Tue, 28 Apr 2015 01:01:36 +0000 (UTC)
Received: by smtp.webfaction.com (Postfix)
	id 0A7152104B13; Tue, 28 Apr 2015 01:01:36 +0000 (UTC)
Date: Tue, 28 Apr 2015 01:01:36 +0000 (UTC)
From: MAILER-DAEMON@smtp.webfaction.com (Mail Delivery System)
Subject: Undelivered Mail Returned to Sender
To: website@learnscripture.net
Auto-Submitted: auto-replied
MIME-Version: 1.0
Content-Type: multipart/report; report-type=delivery-status;
	boundary="D6E612104AE9.1430182896/smtp.webfaction.com"
Message-Id: <20150428010136.0A7152104B13@smtp.webfaction.com>

This is a MIME-encapsulated message.

--D6E612104AE9.1430182896/smtp.webfaction.com
Content-Description: Notification
Content-Type: text/plain; charset=us-ascii

This is the mail system at host smtp.webfaction.com.

I'm sorry to have to inform you that your message could not
be delivered to one or more recipients. It's attached below.

For further assistance, please send mail to <postmaster>

If you do so, please include this problem report. You can
delete your own text from the attached returned message.

                   The mail system

<someone@gmail.com>: host gmail-smtp-in.l.google.com[173.194.217.27] said:
    550-5.1.1 The email account that you tried to reach does not exist. Please
    try 550-5.1.1 double-checking the recipient's email address for typos or
    550-5.1.1 unnecessary spaces. Learn more at 550 5.1.1
    http://support.google.com/mail/bin/answer.py?answer=6596 x2si32585921vdb.53
    - gsmtp (in reply to RCPT TO command)

--D6E612104AE9.1430182896/smtp.webfaction.com
Content-Description: Delivery report
Content-Type: message/delivery-status

Reporting-MTA: dns; smtp.webfaction.com
X-Postfix-Queue-ID: D6E612104AE9
X-Postfix-Sender: rfc822; website@learnscripture.net
Arrival-Date: Tue, 28 Apr 2015 01:01:35 +0000 (UTC)

Final-Recipient: rfc822; someone@gmail.com
Original-Recipient: rfc822;someone@gmail.com
Action: failed
Status: 5.1.1
Remote-MTA: dns; gmail-smtp-in.l.google.com
Diagnostic-Code: smtp; 550-5.1.1 The email account that you tried to reach does
    not exist. Please try 550-5.1.1 double-checking the recipient's email
    address for typos or 550-5.1.1 unnecessary spaces. Learn more at 550 5.1.1
    http://support.google.com/mail/bin/answer.py?answer=6596 x2si32585921vdb.53
    - gsmtp

--D6E612104AE9.1430182896/smtp.webfaction.com
Content-Description: Undelivered Message
Content-Type: message/rfc822

Received: from web178.webfaction.com (web178.webfaction.com [75.126.149.9])
	by smtp.webfaction.com (Postfix) with ESMTP id D6E612104AE9
	for <someone@gmail.com>; Tue, 28 Apr 2015 01:01:35 +0000 (UTC)
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit
Subject: Review reminder for LearnScripture.net
From: website@learnscripture.net
To: someone@gmail.com
Date: Tue, 28 Apr 2015 01:01:35 -0000
Message-ID: <20150428010135.5074.60282@web178.webfaction.com>
Auto-Submitted: auto-generated

Hi Joseph,

You've got some Bible verses due for review on LearnScripture.net!

At least one is overdue by 370 days.

To go to your dashboard, click this link:

  http://learnscripture.net/dashboard/?t=Joseph:1Yxtu3:YAlabcJ_hwY5rYmcx1asfB36w2Q

If you want to opt out of these emails or limit the frequency,
you can do so here:

  http://learnscripture.net/account/?t=Joseph:1Yxtu3:YAlabcJ_hwY5rYmcx1asfB36w2Q

--
This was an automated email from the learnscripture.net site,
sent out according to your preferences.



--D6E612104AE9.1430182896/smtp.webfaction.com--
"""
        handle_bounce(StringIO.StringIO(bounce_email))

        self.assertEqual(Account.objects.filter(email='someone@gmail.com',
                                                email_bounced__isnull=True).count(),
                         0)
        self.assertEqual(Account.objects.get(email='someone@gmail.com').email_bounced,
                         timezone.make_aware(datetime(2015, 4, 28, 1, 1, 35),
                                             timezone.utc))
