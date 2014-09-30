# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'HttpLog'
        db.create_table(u'tracking_httplog', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('response_data', self.gf('django.db.models.fields.TextField')()),
            ('request_data', self.gf('json_field.fields.JSONField')(default=u'null')),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'tracking', ['HttpLog'])


    def backwards(self, orm):
        # Deleting model 'HttpLog'
        db.delete_table(u'tracking_httplog')


    models = {
        u'tracking.httplog': {
            'Meta': {'object_name': 'HttpLog'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'request_data': ('json_field.fields.JSONField', [], {'default': "u'null'"}),
            'response_data': ('django.db.models.fields.TextField', [], {})
        },
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