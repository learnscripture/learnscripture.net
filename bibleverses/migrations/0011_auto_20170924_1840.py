# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-24 18:40
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0010_auto_20170924_1839'),
    ]

    operations = [
        migrations.RenameField(
            model_name='verse',
            old_name='verse_number',
            new_name='first_verse_number',
        ),
    ]