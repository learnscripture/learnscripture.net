# -*- coding: utf-8 -*-

from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.utils import timezone

from app_metrics.models import Metric
from app_metrics.utils import create_metric

class Migration(DataMigration):

    def forwards(self, orm):
        from datetime import datetime, timedelta, date
        create_metric(name='Active accounts', slug='accounts_active')
        create_metric(name='Active identities', slug='identities_active')

        from learnscripture.metrics import record_active_accounts
        n = timezone.now()
        # Go back to Feb 1st. These stats aren't accurate, but good enough.
        while n.date() > date(2012, 02, 01):
            record_active_accounts(now=n)
            n = n - timedelta(days=1)

    def backwards(self, orm):
        Metric.objects.filter(slug='accounts_active').delete()
        Metric.objects.filter(slug='identities_active').delete()


    models = {
        
    }

    complete_apps = ['learnscripture']
    symmetrical = True
