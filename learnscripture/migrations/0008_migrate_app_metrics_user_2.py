# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field email_recipients on 'MetricSet'
        db.create_table(u'app_metrics_metricset_email_recipients', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('metricset', models.ForeignKey(orm[u'app_metrics.metricset'], null=False)),
            ('account', models.ForeignKey(orm[u'accounts.account'], null=False))
        ))
        db.create_unique(u'app_metrics_metricset_email_recipients', ['metricset_id', 'account_id'])


    def backwards(self, orm):
        # Removing M2M table for field email_recipients on 'MetricSet'
        db.delete_table('app_metrics_metricset_email_recipients')


    models = {
        u'accounts.account': {
            'Meta': {'ordering': "['username']", 'object_name': 'Account'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'has_installed_android_app': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_hellbanned': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_tester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_under_13': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'last_reminder_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'remind_after': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'remind_every': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'app_metrics.gauge': {
            'Meta': {'object_name': 'Gauge'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'current_value': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '15', 'decimal_places': '6'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '60'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        u'app_metrics.metric': {
            'Meta': {'object_name': 'Metric'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '60'})
        },
        u'app_metrics.metricday': {
            'Meta': {'object_name': 'MetricDay'},
            'created': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metric': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app_metrics.Metric']"}),
            'num': ('django.db.models.fields.BigIntegerField', [], {'default': '0'})
        },
        u'app_metrics.metricitem': {
            'Meta': {'object_name': 'MetricItem'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metric': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app_metrics.Metric']"}),
            'num': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        u'app_metrics.metricmonth': {
            'Meta': {'object_name': 'MetricMonth'},
            'created': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metric': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app_metrics.Metric']"}),
            'num': ('django.db.models.fields.BigIntegerField', [], {'default': '0'})
        },
        u'app_metrics.metricset': {
            'Meta': {'object_name': 'MetricSet'},
            'email_recipients': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['accounts.Account']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metrics': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['app_metrics.Metric']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'no_email': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_daily': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'send_monthly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_weekly': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'app_metrics.metricweek': {
            'Meta': {'object_name': 'MetricWeek'},
            'created': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metric': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app_metrics.Metric']"}),
            'num': ('django.db.models.fields.BigIntegerField', [], {'default': '0'})
        },
        u'app_metrics.metricyear': {
            'Meta': {'object_name': 'MetricYear'},
            'created': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metric': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app_metrics.Metric']"}),
            'num': ('django.db.models.fields.BigIntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['app_metrics']

    depends_on = [
        ('app_metrics', '0003_auto__add_gauge'),
        ]
