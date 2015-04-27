# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20150407_0923'),
    ]

    operations = [
        migrations.AddField(
            model_name='identity',
            name='enable_vibration',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
