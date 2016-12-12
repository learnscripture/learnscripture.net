from datetime import timedelta

from app_metrics.models import Metric, MetricDay
from django.utils import timezone

from accounts.models import get_active_account_count, get_active_identity_count


def record_active_accounts(now=None):
    if now is None:
        now = timezone.now()

    today = now.astimezone(timezone.utc).date()
    start = now - timedelta(days=7)
    end = now

    md1, b = MetricDay.objects.get_or_create(metric=Metric.objects.get(slug='accounts_active'),
                                             created=today)
    md1.num = get_active_account_count(start, end)
    md1.save()

    md2, b = MetricDay.objects.get_or_create(metric=Metric.objects.get(slug='identities_active'),
                                             created=today)
    md2.num = get_active_identity_count(start, end)
    md2.save()
