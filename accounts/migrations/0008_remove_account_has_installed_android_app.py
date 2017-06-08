# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_remove_identity_track_learning'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='has_installed_android_app',
        ),
    ]
