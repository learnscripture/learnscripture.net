# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Account'
        db.create_table('accounts_account', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')()),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')()),
            ('subscription', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('paid_until', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('accounts', ['Account'])

        # Adding model 'Identity'
        db.create_table('accounts_identity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.OneToOneField')(default=None, to=orm['accounts.Account'], unique=True, null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('accounts', ['Identity'])

    def backwards(self, orm):
        # Deleting model 'Account'
        db.delete_table('accounts_account')

        # Deleting model 'Identity'
        db.delete_table('accounts_identity')

    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'paid_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'subscription': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'accounts.identity': {
            'Meta': {'object_name': 'Identity'},
            'account': ('django.db.models.fields.related.OneToOneField', [], {'default': 'None', 'to': "orm['accounts.Account']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['accounts']
