# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-08 12:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scores', '0004_auto_20160306_2013'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='reason',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Verse tested'), (1, 'Verse revised'), (2, 'Review completed'), (3, 'Perfect!'), (4, 'Verse fully learnt'), (5, 'Earned award')]),
        ),
    ]
