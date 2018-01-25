# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-25 12:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
        ('events', '0009_auto_20180118_0931'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='groups.Group'),
        ),
    ]