# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.rename_column('bibleverses_userversestatus', 'bible_verse_number', 'text_order')

    def backwards(self, orm):
        db.rename_column('bibleverses_userversestatus', 'text_order', 'bible_verse_number')

    models = {
        'accounts.account': {
            'Meta': {'ordering': "['username']", 'object_name': 'Account'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_hellbanned': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
        'accounts.identity': {
            'Meta': {'object_name': 'Identity'},
            'account': ('django.db.models.fields.related.OneToOneField', [], {'default': 'None', 'to': "orm['accounts.Account']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_bible_version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.TextVersion']", 'null': 'True', 'blank': 'True'}),
            'enable_animations': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interface_theme': ('django.db.models.fields.CharField', [], {'default': "'calm'", 'max_length': '30'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'referrals'", 'null': 'True', 'blank': 'True', 'to': "orm['accounts.Account']"}),
            'testing_method': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'})
        },
        'bibleverses.qapair': {
            'Meta': {'unique_together': "[('catechism', 'order'), ('catechism', 'reference')]", 'object_name': 'QAPair'},
            'answer': ('django.db.models.fields.TextField', [], {}),
            'catechism': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'qapairs'", 'to': "orm['bibleverses.TextVersion']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'bibleverses.textversion': {
            'Meta': {'ordering': "('short_name',)", 'object_name': 'TextVersion'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'text_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'})
        },
        'bibleverses.userversestatus': {
            'Meta': {'unique_together': "[('for_identity', 'verse_set', 'reference', 'version')]", 'object_name': 'UserVerseStatus'},
            'added': ('django.db.models.fields.DateTimeField', [], {}),
            'first_seen': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'for_identity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'verse_statuses'", 'to': "orm['accounts.Identity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignored': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_tested': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'memory_stage': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'next_test_due': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'strength': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'text_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'verse_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.VerseSet']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.TextVersion']"})
        },
        'bibleverses.verse': {
            'Meta': {'ordering': "('bible_verse_number',)", 'unique_together': "[('bible_verse_number', 'version'), ('reference', 'version')]", 'object_name': 'Verse'},
            'bible_verse_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'book_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'chapter_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'text_tsv': ('bibleverses.fields.VectorField', [], {'null': 'True'}),
            'verse_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.TextVersion']"})
        },
        'bibleverses.versechoice': {
            'Meta': {'unique_together': "[('verse_set', 'reference')]", 'object_name': 'VerseChoice'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'set_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'verse_set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'verse_choices'", 'to': "orm['bibleverses.VerseSet']"})
        },
        'bibleverses.verseset': {
            'Meta': {'object_name': 'VerseSet'},
            'additional_info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'breaks': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'verse_sets_created'", 'to': "orm['accounts.Account']"}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'passage_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '203'}),
            'popularity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'set_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '50', 'populate_from': 'None', 'unique_with': '()'})
        }
    }

    complete_apps = ['bibleverses']
