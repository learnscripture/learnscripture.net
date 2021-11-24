from datetime import datetime
from functools import wraps

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Account

from .mailgun import verify_webhook


def b(s):
    return s.encode("ascii")


def ensure_from_mailgun(f):
    @wraps(f)
    def func(request, *args, **kwargs):

        if not verify_webhook(
            b(settings.MAILGUN_API_KEY),
            b(request.POST.get("token", "")),
            b(request.POST.get("timestamp", "")),
            b(request.POST.get("signature", "")),
        ):
            return HttpResponseForbidden("Not a real Mailgun request, ignoring.")

        # Prevent replay:
        if not check_mailgun_timestamp(request):
            return HttpResponseForbidden("Old timestamp, ignoring.")

        return f(request, *args, **kwargs)

    return func


def check_mailgun_timestamp(request):
    timestamp_s = request.POST.get("timestamp", "")
    now = timezone.now()
    timestamp_datetime = datetime.fromtimestamp(int(timestamp_s))
    return (now.date() - timestamp_datetime.date()).days < 2  # < 2 days


@csrf_exempt
@ensure_from_mailgun
def mailgun_bounce_notification(request):
    recipient = request.POST["recipient"]
    bounced_date = timezone.make_aware(datetime.fromtimestamp(int(request.POST["timestamp"])))
    mark_email_bounced(recipient, bounced_date)
    return HttpResponse("OK!")


def mark_email_bounced(email_address, bounce_date):
    Account.objects.filter(email=email_address, email_bounced__isnull=True).update(email_bounced=bounce_date)
