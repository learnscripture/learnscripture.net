# -*- coding: utf-8 -*-
import datetime

from app_metrics.utils import create_metric, metric
from app_metrics.models import Metric, MetricItem
from south.db import db
from south.v2 import DataMigration
from django.db import models

from accounts.models import Account
from scores.models import ScoreLog, ScoreReason

class Migration(DataMigration):

    def forwards(self, orm):
        new_account_m = create_metric(name='New Account', slug='new_account')
        create_metric(name='New Identity', slug='new_identity')
        create_metric(name='Login', slug='login')
        verse_started_m = create_metric(name='Verse started', slug='verse_started')
        verse_tested_m = create_metric(name='Verse tested', slug='verse_tested')
        create_metric(name='Verse completed', slug='verse_completed')

        # Fill up old data
        for account in Account.objects.all():
            MetricItem.objects.create(metric=new_account_m,
                                      num=1,
                                      created=account.date_joined.date())

        for scorelog in ScoreLog.objects.all():
            if scorelog.reason == ScoreReason.VERSE_TESTED:
                MetricItem.objects.create(metric=verse_started_m, num=1,
                                          created=scorelog.created.date())
                MetricItem.objects.create(metric=verse_tested_m, num=1,
                                          created=scorelog.created.date())

            elif scorelog.reason == ScoreReason.VERSE_REVISED:
                MetricItem.objects.create(metric=verse_tested_m, num=1,
                                          created=scorelog.created.date())
        # No verses complete at time of migration, don't need to fix that

    def backwards(self, orm):
        Metric.objects.all().delete()
        MetricItem.objects.all().delete()

    models = {
    }

    complete_apps = ['learnscripture', 'accounts', 'scores']
    symmetrical = True

    depends_on = [
        ('accounts', '0011_auto__add_field_identity_referred_by'),
        ('scores', '0001_initial'),
        ]
