# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Event'
        db.create_table('events_event', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message_html', self.gf('django.db.models.fields.TextField')()),
            ('event_type', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('weight', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=10)),
            ('event_data', self.gf('jsonfield.fields.JSONField')(blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 5, 7, 16, 35, 32, 332225), db_index=True)),
        ))
        db.send_create_signal('events', ['Event'])

    def backwards(self, orm):
        # Deleting model 'Event'
        db.delete_table('events_event')

    models = {
        'events.event': {
            'Meta': {'object_name': 'Event'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 5, 7, 16, 35, 32, 336453)', 'db_index': 'True'}),
            'event_data': ('jsonfield.fields.JSONField', [], {'blank': 'True'}),
            'event_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_html': ('django.db.models.fields.TextField', [], {}),
            'weight': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '10'})
        }
    }

    complete_apps = ['events']