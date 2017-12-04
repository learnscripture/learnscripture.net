# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-04 11:43
from __future__ import unicode_literals

from django.db import migrations


def forwards(apps, schema_editor):
    TextVersion = apps.get_model('bibleverses.TextVersion')
    TextVersion.objects.filter(text_type="1").update(text_type="BIBLE")
    TextVersion.objects.filter(text_type="2").update(text_type="CATECHISM")


def backwards(apps, schema_editor):
    TextVersion = apps.get_model('bibleverses.TextVersion')
    TextVersion.objects.filter(text_type="BIBLE").update(text_type="1")
    TextVersion.objects.filter(text_type="CATECHISM").update(text_type="2")


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0026_auto_20171204_1143'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
