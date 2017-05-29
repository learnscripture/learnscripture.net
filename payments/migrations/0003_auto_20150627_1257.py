# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_donationdrive_target'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='paypal_ipn',
            field=models.ForeignKey(related_name='payments', to='ipn.PayPalIPN', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
