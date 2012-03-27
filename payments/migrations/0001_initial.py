# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Currency'
        db.create_table('payments_currency', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('symbol', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('payments', ['Currency'])

        # Adding model 'Price'
        db.create_table('payments_price', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('currency', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['payments.Currency'])),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('days', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('valid_until', self.gf('django.db.models.fields.DateTimeField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('payments', ['Price'])

    def backwards(self, orm):
        # Deleting model 'Currency'
        db.delete_table('payments_currency')

        # Deleting model 'Price'
        db.delete_table('payments_price')

    models = {
        'payments.currency': {
            'Meta': {'object_name': 'Currency'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'symbol': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'payments.price': {
            'Meta': {'object_name': 'Price'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'currency': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['payments.Currency']"}),
            'days': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'valid_until': ('django.db.models.fields.DateTimeField', [], {})
        }
    }

    complete_apps = ['payments']