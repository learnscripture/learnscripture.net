# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-26 08:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('awards', '0003_auto_20171208_0412'),
    ]

    operations = [
        migrations.AlterField(
            model_name='award',
            name='award_type',
            field=models.CharField(choices=[('STUDENT', 'Student'), ('MASTER', 'Master'), ('SHARER', 'Sharer'), ('TREND_SETTER', 'Trend setter'), ('ACE', 'Ace'), ('RECRUITER', 'Recruiter'), ('WEEKLY_CHAMPION', 'Weekly champion'), ('REIGNING_WEEKLY_CHAMPION', 'Reigning weekly champion'), ('ADDICT', 'Addict'), ('ORGANIZER', 'Organizer'), ('CONSISTENT_LEARNER', 'Consistent learner')], max_length=40),
        ),
    ]