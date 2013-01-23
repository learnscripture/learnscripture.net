# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        for award in orm['awards.Award'].objects.filter(award_type=4, # Ace
                                                        level=3,
                                                        ).select_related('account'):
            orm['accounts.Notice'].objects.create(for_identity=award.account.identity,
                                                  message_html="We've re-adjusted the points awarded for 'Ace' awards to better suit our priorities, so your points have gone down - sorry!")


    def backwards(self, orm):
        pass

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
        u'accounts.identity': {
            'Meta': {'object_name': 'Identity'},
            'account': ('django.db.models.fields.related.OneToOneField', [], {'default': 'None', 'to': u"orm['accounts.Account']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_bible_version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bibleverses.TextVersion']", 'null': 'True', 'blank': 'True'}),
            'enable_animations': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interface_theme': ('django.db.models.fields.CharField', [], {'default': "'calm'", 'max_length': '30'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'referrals'", 'null': 'True', 'blank': 'True', 'to': u"orm['accounts.Account']"}),
            'testing_method': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'})
        },
        u'accounts.notice': {
            'Meta': {'object_name': 'Notice'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'for_identity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notices'", 'to': u"orm['accounts.Identity']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_html': ('django.db.models.fields.TextField', [], {}),
            'seen': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        u'awards.award': {
            'Meta': {'object_name': 'Award'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'awards'", 'to': u"orm['accounts.Account']"}),
            'award_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'bibleverses.textversion': {
            'Meta': {'ordering': "('short_name',)", 'object_name': 'TextVersion'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'text_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'})
        },
        u'scores.scorelog': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'ScoreLog'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'score_logs'", 'to': u"orm['accounts.Account']"}),
            'accuracy': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'reason': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'scores.totalscore': {
            'Meta': {'object_name': 'TotalScore'},
            'account': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'total_score'", 'unique': 'True', 'to': u"orm['accounts.Account']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        }
    }

    complete_apps = ['accounts', 'scores', 'awards']
    symmetrical = True
