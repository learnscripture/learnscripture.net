# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-24 18:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0011_auto_20170924_1840'),
    ]

    operations = [
        migrations.AddField(
            model_name='verse',
            name='last_verse_number',
            field=models.PositiveSmallIntegerField(null=True),
        ),
    ]
