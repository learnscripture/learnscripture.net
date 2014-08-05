# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        db.execute("SET CONSTRAINTS ALL DEFERRED;")
        for v in orm['bibleverses.TextVersion'].objects.all():
            orm['bibleverses.WordSuggestionData'].objects.filter(version=v).update(version_slug=v.slug)


    def backwards(self, orm):
        db.execute("SET CONSTRAINTS ALL DEFERRED;")
        for v in orm['bibleverses.TextVersion'].objects.all():
            orm['bibleverses.WordSuggestionData'].objects.filter(version_slug=v.slug).update(version=v)

    models = {
        u'accounts.account': {
            'Meta': {'ordering': "[u'username']", 'object_name': 'Account'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'enable_commenting': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'following': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'followers'", 'blank': 'True', 'to': u"orm['accounts.Account']"}),
            'has_installed_android_app': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_hellbanned': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_moderator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'desktop_testing_method': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'enable_animations': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interface_theme': ('django.db.models.fields.CharField', [], {'default': "u'calm'", 'max_length': '30'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "u'referrals'", 'null': 'True', 'blank': 'True', 'to': u"orm['accounts.Account']"}),
            'touchscreen_testing_method': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'})
        },
        u'bibleverses.qapair': {
            'Meta': {'unique_together': "[('catechism', 'order'), ('catechism', 'reference')]", 'object_name': 'QAPair'},
            'answer': ('django.db.models.fields.TextField', [], {}),
            'catechism': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'qapairs'", 'to': u"orm['bibleverses.TextVersion']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'bibleverses.textversion': {
            'Meta': {'ordering': "['short_name']", 'object_name': 'TextVersion'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'text_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'})
        },
        u'bibleverses.userversestatus': {
            'Meta': {'unique_together': "[('for_identity', 'verse_set', 'reference', 'version')]", 'object_name': 'UserVerseStatus'},
            'added': ('django.db.models.fields.DateTimeField', [], {}),
            'first_seen': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'for_identity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'verse_statuses'", 'to': u"orm['accounts.Identity']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignored': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_tested': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'memory_stage': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'next_test_due': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'strength': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'text_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'verse_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bibleverses.VerseSet']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bibleverses.TextVersion']"})
        },
        u'bibleverses.verse': {
            'Meta': {'ordering': "('bible_verse_number',)", 'unique_together': "[('bible_verse_number', 'version'), ('reference', 'version')]", 'object_name': 'Verse'},
            'bible_verse_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'book_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'chapter_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'missing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'text_tsv': ('bibleverses.fields.VectorField', [], {'null': 'True'}),
            'verse_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bibleverses.TextVersion']"})
        },
        u'bibleverses.versechoice': {
            'Meta': {'unique_together': "[('verse_set', 'reference')]", 'object_name': 'VerseChoice'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'set_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'verse_set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'verse_choices'", 'to': u"orm['bibleverses.VerseSet']"})
        },
        u'bibleverses.verseset': {
            'Meta': {'object_name': 'VerseSet'},
            'additional_info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'breaks': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'verse_sets_created'", 'to': u"orm['accounts.Account']"}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'passage_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '203'}),
            'popularity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'set_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '50', 'populate_from': 'None', 'unique_with': '()'})
        },
        u'bibleverses.wordsuggestiondata': {
            'Meta': {'unique_together': "[('version', 'reference')]", 'object_name': 'WordSuggestionData'},
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'suggestions': ('jsonfield.fields.JSONField', [], {}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'word_suggestion_data'", 'to': u"orm['bibleverses.TextVersion']"}),
            'version_slug': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20'})
        }
    }

    complete_apps = ['bibleverses']
    symmetrical = True
