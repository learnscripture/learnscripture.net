# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Group'
        db.create_table('groups_group', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique=True, max_length=50, populate_from=None, unique_with=())),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 5, 23, 15, 24, 34, 348363))),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='groups_created', to=orm['accounts.Account'])),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('open', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('groups', ['Group'])

        # Adding model 'Membership'
        db.create_table('groups_membership', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(related_name='memberships', to=orm['accounts.Account'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='account_set', to=orm['groups.Group'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 5, 23, 15, 24, 34, 349911))),
        ))
        db.send_create_signal('groups', ['Membership'])

        # Adding model 'Invitation'
        db.create_table('groups_invitation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(related_name='invitations', to=orm['accounts.Account'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['groups.Group'])),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='invitations_created', to=orm['accounts.Account'])),
        ))
        db.send_create_signal('groups', ['Invitation'])

    def backwards(self, orm):
        # Deleting model 'Group'
        db.delete_table('groups_group')

        # Deleting model 'Membership'
        db.delete_table('groups_membership')

        # Deleting model 'Invitation'
        db.delete_table('groups_invitation')

    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 5, 23, 15, 24, 34, 364336)'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_hellbanned': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_tester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_under_13': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 5, 23, 15, 24, 34, 364163)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'last_reminder_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'paid_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'remind_after': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'remind_every': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'subscription': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'groups.group': {
            'Meta': {'object_name': 'Group'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 5, 23, 15, 24, 34, 365792)'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups_created'", 'to': "orm['accounts.Account']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'groups'", 'symmetrical': 'False', 'through': "orm['groups.Membership']", 'to': "orm['accounts.Account']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'open': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '50', 'populate_from': 'None', 'unique_with': '()'})
        },
        'groups.invitation': {
            'Meta': {'object_name': 'Invitation'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations'", 'to': "orm['accounts.Account']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_created'", 'to': "orm['accounts.Account']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'groups.membership': {
            'Meta': {'object_name': 'Membership'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['accounts.Account']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 5, 23, 15, 24, 34, 367336)'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'account_set'", 'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['groups']