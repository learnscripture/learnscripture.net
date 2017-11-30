# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-30 10:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_identity_new_learn_page'),
    ]

    operations = [
        migrations.AlterField(
            model_name='identity',
            name='desktop_testing_method',
            field=models.CharField(choices=[(0, 'Type whole word - recommended for full keyboards and normal typing skills'), (1, 'Type first letter - recommended for slower typers'), (2, 'Choose from word list - recommended for handheld devices. Only available for English translations')], default=0, max_length=20),
        ),
        migrations.AlterField(
            model_name='identity',
            name='touchscreen_testing_method',
            field=models.CharField(choices=[(0, 'Type whole word - recommended for full keyboards and normal typing skills'), (1, 'Type first letter - recommended for slower typers'), (2, 'Choose from word list - recommended for handheld devices. Only available for English translations')], default=2, max_length=20),
        ),
    ]
