# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0003_auto_20161209_1826'),
    ]

    operations = [
        migrations.AddField(
            model_name='verse',
            name='text_fetched_at',
            field=models.DateTimeField(null=True),
        ),
    ]
