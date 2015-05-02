from __future__ import absolute_import, unicode_literals

from datetime import timedelta, datetime
import email.parser
import email.utils

from django.conf import settings
from django.contrib.sites.models import get_current_site
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.template import loader
from django.utils import timezone
from django.utils.html import format_html

from accounts.models import Account
from accounts.tokens import get_login_token

import logging
logger = logging.getLogger(__name__)


def send_email_reminders():
    current_site = get_current_site(None)
    # remind_after == 0 mean 'never'
    for account in Account.objects.send_reminders_to().select_related('identity'):
        # The whole loop could take some time, so we put this line inside loop:
        n = timezone.now()

        # We will never send emails if the verse is overdue by less than
        # 'remind_after' days, so use that to adjust our 'now' value and do DB
        # filtering.
        if account.identity is None:
            # can occur in tests
            continue

        v = account.identity.first_overdue_verse(n + timedelta(account.remind_after))
        if v is None:
            continue

        send_reminder = False
        if (account.last_reminder_sent is not None and
            account.last_reminder_sent > v.next_test_due):
            # Reminder has been sent, so we are in the region
            # for repeat reminders.
            if (account.remind_every > 0 and  # remind_every == 0 'means' never
                (n - account.last_reminder_sent).days >= account.remind_every):
                send_reminder = True
        else:
            # Reminder not sent, check for first reminder.
            if (n - v.next_test_due).days >= account.remind_after:
                send_reminder = True

        if not send_reminder:
            continue

        c = {'account': account,
             'overdue_by': (n - v.next_test_due).days,
             'domain': current_site.domain,
             'site_name': current_site.name,
             'login_token': get_login_token(account),
             }

        EmailMessage(
            subject='Review reminder for LearnScripture.net',
            body=loader.render_to_string("learnscripture/reminder_email.txt", c),
            from_email=settings.REMINDER_EMAIL,
            to=[account.email],
            headers={'Auto-Submitted': 'auto-generated'},
        ).send()
        Account.objects.filter(id=account.id).update(last_reminder_sent=n)


def handle_bounce(email_file):
    p = email.parser.Parser()
    msg = p.parse(email_file)

    if msg.get_content_type() != 'multipart/report':
        logger.warn("Unrecognised content type '%s' in bounce email", msg.get_content_type())
        return

    bounced_email_address = None
    bounced_date = None
    if len(msg.get_payload()) > 1:
        status = msg.get_payload(1)
        if status.get_content_type() == 'message/delivery-status':
            for dsn in status.get_payload():
                if dsn.get('action', '').lower() == 'failed':
                    address_type, email_address = dsn['Final-Recipient'].split(';')
                    email_address = email_address.strip()
                    if address_type.lower() == 'rfc822':
                        bounced_email_address = email_address

    if bounced_email_address is not None:
        # Attempt to find a date:
        for part in msg.walk():
            for header in ['Date', 'Arrival-Date']:
                if header in part:
                    bounced_date = parse_email_date(part[header])

    if bounced_email_address is not None:
        if bounced_date is None:
            bounced_date = timezone.now()
        mark_email_bounced(bounced_email_address, bounced_date)


def parse_email_date(date_string):
    date_tuple = email.utils.parsedate_tz(date_string)
    if date_tuple:
        return timezone.make_aware(datetime.fromtimestamp(email.utils.mktime_tz(date_tuple)),
                                   timezone.utc)


def mark_email_bounced(email_address, bounce_date):
    accounts = Account.objects.filter(email=email_address)
    for account in accounts:
        if account.email_bounced is None:
            account.add_html_notice(
                format_html(
"""Your email address doesn't seem to be working, so we've disabled email reminders. """
"""Please update your <a href="{0}">account details</a>.""",
                    reverse('account_details')))
        account.email_bounced = bounce_date
        account.save()
