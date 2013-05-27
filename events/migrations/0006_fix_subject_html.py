# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        # Use imports here, instead of 'orm[]' etc. because we need methods on models.
        from events.models import Event, EventType, NewCommentEvent
        from comments.models import Comment
        for event in Event.objects.filter(event_type=EventType.NEW_COMMENT):
            event_logic = NewCommentEvent(
                account=event.account,
                comment=Comment.objects.get(id=event.event_data['comment_id'])
                )
            event.message_html = event_logic.event.message_html
            event.save()


    def backwards(self, orm):
        pass

    models = {
        u'accounts.account': {
            'Meta': {'ordering': "['username']", 'object_name': 'Account'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'following': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'followers'", 'symmetrical': 'False', 'to': u"orm['accounts.Account']"}),
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
        }
    }

    complete_apps = ['events']
    symmetrical = True
