# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BibleVersion'
        db.create_table('bibleverses_bibleversion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('short_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('slug', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('full_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('bibleverses', ['BibleVersion'])

    def backwards(self, orm):
        # Deleting model 'BibleVersion'
        db.delete_table('bibleverses_bibleversion')

    models = {
        'bibleverses.bibleversion': {
            'Meta': {'object_name': 'BibleVersion'},
            'full_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        }
    }

    complete_apps = ['bibleverses']