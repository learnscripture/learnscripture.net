# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-18 07:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0018_auto_20171018_0654'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='versechoice',
            unique_together=set([('verse_set', 'localized_reference'), ('verse_set', 'internal_reference')]),
        ),
    ]