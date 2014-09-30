# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TrackingSnapshot'
        db.create_table(u'tracking_trackingsnapshot', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('model_path', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('snapshot_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('applied', self.gf('django.db.models.fields.BooleanField')()),
            ('old_fields', self.gf('json_field.fields.JSONField')(default=u'null')),
            ('new_fields', self.gf('json_field.fields.JSONField')(default=u'null')),
        ))
        db.send_create_signal(u'tracking', ['TrackingSnapshot'])


    def backwards(self, orm):
        # Deleting model 'TrackingSnapshot'
        db.delete_table(u'tracking_trackingsnapshot')


    models = {
        u'tracking.trackingsnapshot': {
            'Meta': {'ordering': "['created']", 'object_name': 'TrackingSnapshot'},
            'applied': ('django.db.models.fields.BooleanField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'new_fields': ('json_field.fields.JSONField', [], {'default': "u'null'"}),
            'old_fields': ('json_field.fields.JSONField', [], {'default': "u'null'"}),
            'snapshot_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }

    complete_apps = ['tracking']