# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Award'
        db.create_table('awards_award', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('award_type', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('level', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(related_name='awards', to=orm['accounts.Account'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 4, 28, 12, 59, 19, 706465))),
        ))
        db.send_create_signal('awards', ['Award'])

    def backwards(self, orm):
        # Deleting model 'Award'
        db.delete_table('awards_award')

    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 4, 28, 12, 59, 19, 710642)'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_tester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 4, 28, 12, 59, 19, 710464)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'last_reminder_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'paid_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'remind_after': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'remind_every': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'subscription': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'awards.award': {
            'Meta': {'object_name': 'Award'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'awards'", 'to': "orm['accounts.Account']"}),
            'award_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 4, 28, 12, 59, 19, 711965)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        }
    }

    complete_apps = ['awards']
    depends_on = [
        ('accounts', '0011_auto__add_field_identity_referred_by'),
        ]
