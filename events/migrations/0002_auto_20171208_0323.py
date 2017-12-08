# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-08 03:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='event_type',
            field=models.CharField(choices=[('GENERAL', 'General'), ('NEW_ACCOUNT', 'New account'), ('AWARD_RECEIVED', 'Award received'), ('POINTS_MILESTONE', 'Points milestone'), ('VERSES_STARTED_MILESTONE', 'Verses started milestone'), ('VERSES_FINISHED_MILESTONE', 'Verses finished milestone'), ('VERSE_SET_CREATED', 'Verse set created'), ('STARTED_LEARNING_VERSE_SET', 'Started learning a verse set'), ('AWARD_LOST', 'Award lost'), ('GROUP_JOINED', 'Group joined'), ('GROUP_CREATED', 'Group created'), ('STARTED_LEARNING_CATECHISM', 'Started learning catechism'), ('NEW_COMMENT', 'New comment')], max_length=40),
        ),
    ]