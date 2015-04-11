# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('events', '0001_initial'),
        ('bibleverses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notice',
            name='related_event',
            field=models.ForeignKey(blank=True, to='events.Event', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='identity',
            name='account',
            field=models.OneToOneField(null=True, default=None, blank=True, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='identity',
            name='default_bible_version',
            field=models.ForeignKey(blank=True, to='bibleverses.TextVersion', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='identity',
            name='referred_by',
            field=models.ForeignKey(related_name='referrals', default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='account',
            name='following',
            field=models.ManyToManyField(related_name='followers', to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
    ]
