# -*- coding: utf-8 -*-
import datetime

from app_metrics.utils import create_metric, metric
from app_metrics.models import Metric, MetricItem
from south.db import db
from south.v2 import DataMigration
from django.db import models

from scores.models import ScoreReason

class Migration(DataMigration):

    def forwards(self, orm):
        new_account_m = create_metric(name='New Account', slug='new_account')
        create_metric(name='New Identity', slug='new_identity')
        create_metric(name='Login', slug='login')
        verse_started_m = create_metric(name='Verse started', slug='verse_started')
        verse_tested_m = create_metric(name='Verse tested', slug='verse_tested')
        create_metric(name='Verse completed', slug='verse_completed')

        # Fill up old data
        for account in orm['accounts.Account'].objects.all():
            MetricItem.objects.create(metric=new_account_m,
                                      num=1,
                                      created=account.date_joined.date())

        for scorelog in orm['scores.ScoreLog'].objects.all():
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
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 3, 21, 22, 48, 41, 19771)'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_tester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 3, 21, 22, 48, 41, 19577)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'paid_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'remind_after': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'remind_every': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'subscription': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'accounts.identity': {
            'Meta': {'object_name': 'Identity'},
            'account': ('django.db.models.fields.related.OneToOneField', [], {'default': 'None', 'to': "orm['accounts.Account']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 3, 21, 22, 48, 41, 20823)'}),
            'default_bible_version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.BibleVersion']", 'null': 'True', 'blank': 'True'}),
            'enable_animations': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interface_theme': ('django.db.models.fields.CharField', [], {'default': "'calm'", 'max_length': '30'}),
            'testing_method': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'})
        },
        'bibleverses.bibleversion': {
            'Meta': {'ordering': "('short_name',)", 'object_name': 'BibleVersion'},
            'full_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'})
        },
        'scores.scorelog': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'ScoreLog'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'score_logs'", 'to': "orm['accounts.Account']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'reason': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'scores.totalscore': {
            'Meta': {'object_name': 'TotalScore'},
            'account': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['accounts.Account']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
    }

    complete_apps = ['learnscripture', 'accounts', 'scores']
    symmetrical = True

    depends_on = [
        ('accounts', '0011_auto__add_field_identity_referred_by'),
        ('scores', '0001_initial'),
        ]
