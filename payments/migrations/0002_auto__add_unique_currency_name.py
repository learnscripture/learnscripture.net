# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding unique constraint on 'Currency', fields ['name']
        db.create_unique('payments_currency', ['name'])

    def backwards(self, orm):
        # Removing unique constraint on 'Currency', fields ['name']
        db.delete_unique('payments_currency', ['name'])

    models = {
        'payments.currency': {
            'Meta': {'object_name': 'Currency'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
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