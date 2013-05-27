# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        GROUP_JOINED = 10
        GROUP_CREATED = 11
        for comment in (orm['comments.Comment'].objects
                        .filter(event__event_type__in=[GROUP_JOINED,
                                                       GROUP_CREATED])
                        .select_related('event')):
            comment.group_id = comment.event.event_data['group_id']
            comment.save()

    def backwards(self, orm):
        pass

    models = {
        u'accounts.account': {
            'Meta': {'ordering': "['username']", 'object_name': 'Account'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'has_installed_android_app': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_hellbanned': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_moderator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_tester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_under_13': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'last_reminder_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'remind_after': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'remind_every': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'comments.comment': {
            'Meta': {'object_name': 'Comment'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['accounts.Account']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['events.Event']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'comments'", 'null': 'True', 'to': u"orm['groups.Group']"}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {})
        },
        u'events.event': {
            'Meta': {'object_name': 'Event'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.Account']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'event_data': ('jsonfield.fields.JSONField', [], {'blank': 'True'}),
            'event_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_html': ('django.db.models.fields.TextField', [], {}),
            'parent_event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['events.Event']", 'null': 'True', 'blank': 'True'}),
            'weight': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '10'})
        },
        u'groups.group': {
            'Meta': {'ordering': "['name']", 'object_name': 'Group'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups_created'", 'to': u"orm['accounts.Account']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'groups'", 'symmetrical': 'False', 'through': u"orm['groups.Membership']", 'to': u"orm['accounts.Account']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'open': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '50', 'populate_from': 'None', 'unique_with': '()'})
        },
        u'groups.invitation': {
            'Meta': {'object_name': 'Invitation'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations'", 'to': u"orm['accounts.Account']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_created'", 'to': u"orm['accounts.Account']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations'", 'to': u"orm['groups.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'groups.membership': {
            'Meta': {'object_name': 'Membership'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': u"orm['accounts.Account']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': u"orm['groups.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['events', 'groups', 'comments']
    symmetrical = True
