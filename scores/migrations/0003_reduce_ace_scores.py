# -*- coding: utf-8 -*-
import datetime
from datetime import timedelta
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.utils import timezone

OLD_POINTS = {k: 3**(k-1)*1000 for k in range(1, 10)}
NEW_POINTS = {k: 2**(k-1)*1000 for k in range(1, 10)}

ACE_AWARD_TYPE = 4 # from awards.models
AWARD_SCORE_REASON = 5 # from scores.models

class Migration(DataMigration):

    def forwards(self, orm):
        self._migrate_points(orm, OLD_POINTS, NEW_POINTS)

    def _migrate_points(self, orm, FROM_POINTS, TO_POINTS):

        ScoreLog = orm['scores.ScoreLog']
        TotalScore = orm['scores.TotalScore']
        Award = orm['awards.Award']
        Account = orm['accounts.Account']

        # Get all 'Ace' awards

        # We filter to only include ones that were created while the old points
        # system was in place

        for award in Award.objects.filter(award_type=ACE_AWARD_TYPE,
                                          created__lt=datetime.datetime(2013, 1, 23, 0, 23, 0, 0, timezone.utc)
                                          ):
            # Find the corresponding ScoreLog. There should be exactly one.
            # However, we need to use 10 second deltas to give time for processing.
            # Further, sometimes awards can be gained close to each other,
            # and some other awards match the points for Ace awards,
            # so we work out which one is for this award based on score
            scorelogs = ScoreLog.objects.filter(created__gt=award.created - timedelta(seconds=10),
                                                created__lt=award.created + timedelta(seconds=10),
                                                account=award.account,
                                                reason=AWARD_SCORE_REASON)
            matching = [sc for sc in scorelogs if sc.points == FROM_POINTS[award.level]]
            assert len(matching) > 0
            # If more than one match, we pick any, since it doesn't matter
            scorelog = matching[0]
            scorelog.points = TO_POINTS[award.level]
            scorelog.save()

        # Rather than adjust TotalScore as we go, we rewrite it.  This has the
        # advantage that it fixes some discrepancies that exist due to old bugs
        # in scores that didn't round correctly.
        for account in Account.objects.all().annotate(points=models.Sum('score_logs__points')):
            if account.points is None:
                account.points = 0
            ts = account.total_score
            ts.points = account.points
            ts.save()

    def backwards(self, orm):
        self._migrate_points(orm, NEW_POINTS, OLD_POINTS)

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
        u'awards.award': {
            'Meta': {'object_name': 'Award'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'awards'", 'to': u"orm['accounts.Account']"}),
            'award_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
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

    complete_apps = ['awards', 'scores']
    symmetrical = True
