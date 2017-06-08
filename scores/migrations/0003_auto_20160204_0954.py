# -*- coding: utf-8 -*-
from django.db import migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('scores', '0002_scorelog_reference'),
    ]

    operations = [
        migrations.RenameModel('ScoreLog', 'ActionLog'),
    ]
