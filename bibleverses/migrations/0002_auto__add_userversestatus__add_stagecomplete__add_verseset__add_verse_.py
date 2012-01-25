# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = [
        ('accounts', '0001_initial'),
        ]

    def forwards(self, orm):
        # Adding model 'UserVerseStatus'
        db.create_table('bibleverses_userversestatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('for_identity', self.gf('django.db.models.fields.related.ForeignKey')(related_name='verse_statuses', to=orm['accounts.Identity'])),
            ('verse', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bibleverses.VerseChoice'])),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bibleverses.BibleVersion'])),
            ('memory_stage', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('strength', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=3, decimal_places=2)),
            ('first_seen', self.gf('django.db.models.fields.DateTimeField')()),
            ('last_seen', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('bibleverses', ['UserVerseStatus'])

        # Adding model 'StageComplete'
        db.create_table('bibleverses_stagecomplete', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('verse_status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bibleverses.UserVerseStatus'])),
            ('stage_type', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('level', self.gf('django.db.models.fields.DecimalField')(max_digits=3, decimal_places=2)),
            ('accuracy', self.gf('django.db.models.fields.DecimalField')(max_digits=3, decimal_places=2)),
            ('date_completed', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('bibleverses', ['StageComplete'])

        # Adding model 'VerseSet'
        db.create_table('bibleverses_verseset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('set_type', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal('bibleverses', ['VerseSet'])

        # Adding model 'Verse'
        db.create_table('bibleverses_verse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bibleverses.BibleVersion'])),
            ('reference', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('bibleverses', ['Verse'])

        # Adding model 'VerseChoice'
        db.create_table('bibleverses_versechoice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reference', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('verse_set', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='verses', null=True, to=orm['bibleverses.VerseSet'])),
            ('set_order', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal('bibleverses', ['VerseChoice'])

        # Adding unique constraint on 'VerseChoice', fields ['verse_set', 'reference']
        db.create_unique('bibleverses_versechoice', ['verse_set_id', 'reference'])

    def backwards(self, orm):
        # Removing unique constraint on 'VerseChoice', fields ['verse_set', 'reference']
        db.delete_unique('bibleverses_versechoice', ['verse_set_id', 'reference'])

        # Deleting model 'UserVerseStatus'
        db.delete_table('bibleverses_userversestatus')

        # Deleting model 'StageComplete'
        db.delete_table('bibleverses_stagecomplete')

        # Deleting model 'VerseSet'
        db.delete_table('bibleverses_verseset')

        # Deleting model 'Verse'
        db.delete_table('bibleverses_verse')

        # Deleting model 'VerseChoice'
        db.delete_table('bibleverses_versechoice')

    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 24, 14, 54, 13, 533644)'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 24, 14, 54, 13, 533464)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'paid_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'subscription': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'accounts.identity': {
            'Meta': {'object_name': 'Identity'},
            'account': ('django.db.models.fields.related.OneToOneField', [], {'default': 'None', 'to': "orm['accounts.Account']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 24, 14, 54, 13, 532503)'}),
            'default_bible_version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.BibleVersion']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'bibleverses.bibleversion': {
            'Meta': {'object_name': 'BibleVersion'},
            'full_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
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
            'Meta': {'object_name': 'UserVerseStatus'},
            'first_seen': ('django.db.models.fields.DateTimeField', [], {}),
            'for_identity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'verse_statuses'", 'to': "orm['accounts.Identity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_seen': ('django.db.models.fields.DateTimeField', [], {}),
            'memory_stage': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'strength': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '3', 'decimal_places': '2'}),
            'verse': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.VerseChoice']"}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.BibleVersion']"})
        },
        'bibleverses.verse': {
            'Meta': {'object_name': 'Verse'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bibleverses.BibleVersion']"})
        },
        'bibleverses.versechoice': {
            'Meta': {'unique_together': "[('verse_set', 'reference')]", 'object_name': 'VerseChoice'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'set_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'verse_set': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'verses'", 'null': 'True', 'to': "orm['bibleverses.VerseSet']"})
        },
        'bibleverses.verseset': {
            'Meta': {'object_name': 'VerseSet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'set_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        }
    }

    complete_apps = ['bibleverses']
