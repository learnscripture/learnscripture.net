# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-05 10:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0007_auto_20170603_1144'),
    ]

    operations = [
        migrations.AddField(
            model_name='textversion',
            name='language_code',
            field=models.CharField(choices=[('en', 'English')], default='en', max_length=2),
        ),
    ]