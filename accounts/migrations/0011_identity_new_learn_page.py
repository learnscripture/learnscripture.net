# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-29 08:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_auto_20171128_1830'),
    ]

    operations = [
        migrations.AddField(
            model_name='identity',
            name='new_learn_page',
            field=models.BooleanField(default=False, verbose_name='Use new learn page (beta)'),
        ),
    ]
