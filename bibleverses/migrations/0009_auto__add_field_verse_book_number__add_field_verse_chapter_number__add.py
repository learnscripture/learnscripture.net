# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Verse.book_number'
        db.add_column('bibleverses_verse', 'book_number',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Verse.chapter_number'
        db.add_column('bibleverses_verse', 'chapter_number',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1),
                      keep_default=False)

        # Adding field 'Verse.verse_number'
        db.add_column('bibleverses_verse', 'verse_number',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1),
                      keep_default=False)

        # Adding field 'Verse.bible_verse_number'
        db.add_column('bibleverses_verse', 'bible_verse_number',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0),
                      keep_default=False)

        # Adding unique constraint on 'Verse', fields ['version', 'bible_verse_number']
        db.create_unique('bibleverses_verse', ['version_id', 'bible_verse_number'])

    def backwards(self, orm):
        # Removing unique constraint on 'Verse', fields ['version', 'bible_verse_number']
        db.delete_unique('bibleverses_verse', ['version_id', 'bible_verse_number'])

        # Deleting field 'Verse.book_number'
        db.delete_column('bibleverses_verse', 'book_number')

        # Deleting field 'Verse.chapter_number'
        db.delete_column('bibleverses_verse', 'chapter_number')

        # Deleting field 'Verse.verse_number'
        db.delete_column('bibleverses_verse', 'verse_number')

        # Deleting field 'Verse.bible_verse_number'
        db.delete_column('bibleverses_verse', 'bible_verse_number')

    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 30, 11, 52, 12, 918205)'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 30, 11, 52, 12, 918023)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'paid_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'subscription': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'accounts.identity': {
            'Meta': {'object_name': 'Identity'},
            'account': ('django.db.models.fields.related.OneToOneField', [], {'default': 'None', 'to': "orm['accounts.Account']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 30, 11, 52, 12, 913615)'}),
            'default_bible_version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.BibleVersion']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'bibleverses.bibleversion': {
            'Meta': {'object_name': 'BibleVersion'},
            'full_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'})
        },
        'bibleverses.stagecomplete': {
            'Meta': {'object_name': 'StageComplete'},
            'accuracy': ('django.db.models.fields.DecimalField', [], {'max_digits': '3', 'decimal_places': '2'}),
            'date_completed': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.DecimalField', [], {'max_digits': '3', 'decimal_places': '2'}),
            'stage_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'verse_status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.UserVerseStatus']"})
        },
        'bibleverses.userversestatus': {
            'Meta': {'unique_together': "[('for_identity', 'verse_choice', 'version')]", 'object_name': 'UserVerseStatus'},
            'first_seen': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'for_identity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'verse_statuses'", 'to': "orm['accounts.Identity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignored': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_seen': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'memory_stage': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'strength': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '3', 'decimal_places': '2'}),
            'verse_choice': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.VerseChoice']"}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.BibleVersion']"})
        },
        'bibleverses.verse': {
            'Meta': {'unique_together': "[('bible_verse_number', 'version')]", 'object_name': 'Verse'},
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
            'set_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'verse_set': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'verse_choices'", 'null': 'True', 'to': "orm['bibleverses.VerseSet']"})
        },
        'bibleverses.verseset': {
            'Meta': {'object_name': 'VerseSet'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'set_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        }
    }

    complete_apps = ['bibleverses']