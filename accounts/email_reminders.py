from __future__ import absolute_import

from datetime import timedelta

from django.conf import settings
from django.contrib.sites.models import get_current_site
from django.core.mail import send_mail
from django.template import loader
from django.utils import timezone

from accounts.models import Account


def send_email_reminders():
    current_site = get_current_site(None)
    # remind_after == 0 mean 'never'
    for account in Account.objects.filter(remind_after__gt=0).select_related('identity'):
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
            if (account.remind_every > 0 and  #remind_every == 0 'means' never
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
             }
        email = loader.render_to_string("learnscripture/reminder_email.txt", c)

        send_mail('Revision reminder for LearnScripture.net', email,
                  settings.SERVER_EMAIL,
                  [account.email],
                  fail_silently=False)
        Account.objects.filter(id=account.id).update(last_reminder_sent=n)
