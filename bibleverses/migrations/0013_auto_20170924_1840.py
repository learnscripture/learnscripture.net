# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-24 18:40
from __future__ import unicode_literals

from django.db import migrations, models


def forwards(apps, schema_editor):
    Verse = apps.get_model('bibleverses', 'Verse')
    Verse.objects.all().update(last_verse_number=models.F('first_verse_number'))


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0012_verse_last_verse_number'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]