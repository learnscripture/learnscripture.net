# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'UserVerseStatus', fields ['for_identity', 'verse_choice', 'version']
        db.delete_unique('bibleverses_userversestatus', ['for_identity_id', 'verse_choice_id', 'version_id'])


        # Changing field 'UserVerseStatus.verse_choice'
        db.alter_column('bibleverses_userversestatus', 'verse_choice_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bibleverses.VerseChoice'], null=True))
    def backwards(self, orm):

        # Changing field 'UserVerseStatus.verse_choice'
        db.alter_column('bibleverses_userversestatus', 'verse_choice_id', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['bibleverses.VerseChoice']))
        # Adding unique constraint on 'UserVerseStatus', fields ['for_identity', 'verse_choice', 'version']
        db.create_unique('bibleverses_userversestatus', ['for_identity_id', 'verse_choice_id', 'version_id'])

    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 29, 17, 13, 12, 608376)'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 29, 17, 13, 12, 608198)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'paid_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'subscription': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'accounts.identity': {
            'Meta': {'object_name': 'Identity'},
            'account': ('django.db.models.fields.related.OneToOneField', [], {'default': 'None', 'to': "orm['accounts.Account']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 29, 17, 13, 12, 609126)'}),
            'default_bible_version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.BibleVersion']", 'null': 'True', 'blank': 'True'}),
            'enable_animations': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
        'bibleverses.userversestatus': {
            'Meta': {'object_name': 'UserVerseStatus'},
            'added': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'bible_verse_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'first_seen': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'for_identity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'verse_statuses'", 'to': "orm['accounts.Identity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignored': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_tested': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'memory_stage': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'strength': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'verse_choice': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['bibleverses.VerseChoice']", 'null': 'True'}),
            'verse_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.VerseSet']", 'null': 'True'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.BibleVersion']"})
        },
        'bibleverses.verse': {
            'Meta': {'ordering': "('bible_verse_number',)", 'unique_together': "[('bible_verse_number', 'version'), ('reference', 'version')]", 'object_name': 'Verse'},
            'bible_verse_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'book_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'chapter_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'verse_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.BibleVersion']"})
        },
        'bibleverses.versechoice': {
            'Meta': {'unique_together': "[('verse_set', 'reference')]", 'object_name': 'VerseChoice'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'set_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'verse_set': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'verse_choices'", 'null': 'True', 'to': "orm['bibleverses.VerseSet']"})
        },
        'bibleverses.verseset': {
            'Meta': {'object_name': 'VerseSet'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'verse_sets_created'", 'to': "orm['accounts.Account']"}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 29, 17, 13, 12, 607120)'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'popularity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'set_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '50', 'populate_from': 'None', 'unique_with': '()'})
        }
    }

    complete_apps = ['bibleverses']