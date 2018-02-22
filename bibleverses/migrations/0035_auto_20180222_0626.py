# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-02-22 06:26
from __future__ import unicode_literals

from django.db import migrations


def forwards(apps, schema_editor):
    # Fix up bad data caused by bug fixed in c5b66a475c6e
    UserVerseStatus = apps.get_model('bibleverses.UserVerseStatus')
    for uvs in UserVerseStatus.objects.filter(next_test_due__isnull=True,
                                              last_tested__isnull=False):
        print("Fixing UVS.next_test_due", uvs.id, uvs.localized_reference)
        other_uvss = UserVerseStatus.objects.filter(
            for_identity_id=uvs.for_identity_id,
            localized_reference=uvs.localized_reference,
            version_id=uvs.version_id,
            strength__gt=uvs.strength - 0.01,
            strength__lt=uvs.strength + 0.01,
            next_test_due__isnull=False)
        if len(other_uvss) > 0:
            other_uvs = other_uvss[0]
            uvs.next_test_due = other_uvs.next_test_due
            uvs.save()
        else:
            print("Unable to find match")


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0034_userversestatus_early_review_requested'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
