# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SiteNotice'
        db.create_table(u'learnscripture_sitenotice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message_html', self.gf('django.db.models.fields.TextField')()),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('begins', self.gf('django.db.models.fields.DateTimeField')()),
            ('ends', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'learnscripture', ['SiteNotice'])


    def backwards(self, orm):
        # Deleting model 'SiteNotice'
        db.delete_table(u'learnscripture_sitenotice')


    models = {
        u'learnscripture.sitenotice': {
            'Meta': {'object_name': 'SiteNotice'},
            'begins': ('django.db.models.fields.DateTimeField', [], {}),
            'ends': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'message_html': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['learnscripture']