# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_auto_20160204_0925'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='identity',
            name='track_learning',
        ),
    ]
