from __future__ import absolute_import, unicode_literals

import logging
import smtplib
from datetime import timedelta

from django.conf import settings
from django.contrib.sites.models import get_current_site
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.template import loader
from django.utils import timezone
from django.utils.html import format_html

from accounts.models import Account
from accounts.tokens import get_login_token

logger = logging.getLogger(__name__)


def send_email_reminders():
    current_site = get_current_site(None)
    total = 0
    for account in Account.objects.send_reminders_to().select_related('identity'):
        total += send_email_reminder(account, current_site)
    return total


def send_email_reminder(account, current_site):
    n = timezone.now()

    # We will never send emails if the verse is overdue by less than
    # 'remind_after' days, so use that to adjust our 'now' value and do DB
    # filtering.
    if account.identity is None:
        # can occur in tests
        return 0

    v = account.identity.first_overdue_verse(n + timedelta(account.remind_after))
    if v is None:
        return 0

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
        if (account.remind_after > 0 and  # means 'never'
                (n - v.next_test_due).days >= account.remind_after):
            send_reminder = True

    if not send_reminder:
        return 0

    c = {'account': account,
         'overdue_by': (n - v.next_test_due).days,
         'domain': current_site.domain,
         'site_name': current_site.name,
         'login_token': get_login_token(account),
         }

    try:
        EmailMessage(
            subject='Review reminder for LearnScripture.net',
            body=loader.render_to_string("learnscripture/reminder_email.txt", c),
            from_email=settings.REMINDER_EMAIL,
            to=[account.email],
            headers={'Auto-Submitted': 'auto-generated'},
        ).send()
        Account.objects.filter(id=account.id).update(last_reminder_sent=n)
    except smtplib.SMTPRecipientsRefused:
        mark_email_bounced(account.email, n)

    return 1


def mark_email_bounced(email_address, bounce_date):
    accounts = Account.objects.filter(email=email_address)
    for account in accounts:
        if account.email_bounced is None:
            account.add_html_notice(
                format_html(
                    """Your email address doesn't seem to be working, so """
                    """we've disabled email reminders. """
                    """Please update your <a href="{0}">account details</a>.""",
                    reverse('account_details')))
        account.email_bounced = bounce_date
        account.save()
