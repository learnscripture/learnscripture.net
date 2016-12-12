# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.utils import timezone


def forwards(apps, schema_editor):
    TextVersion = apps.get_model('bibleverses', 'TextVersion')
    esv = TextVersion.objects.get(slug='ESV')
    esv.verse_set.exclude(text_saved="").exclude(missing=True).update(text_fetched_at=timezone.now())


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0004_verse_text_fetched_at'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
