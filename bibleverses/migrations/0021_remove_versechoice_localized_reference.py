# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-18 07:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0020_auto_20171018_0706'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='versechoice',
            name='localized_reference',
        ),
    ]