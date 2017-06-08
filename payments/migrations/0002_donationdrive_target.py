# -*- coding: utf-8 -*-
from django.db import models, migrations
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='donationdrive',
            name='target',
            field=models.DecimalField(default=Decimal('0'), max_digits=8, decimal_places=0),
            preserve_default=True,
        ),
    ]
