# Generated by Django 3.1.6 on 2021-03-14 12:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0021_auto_20190812_0722'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subpages', to='cms.page', verbose_name='parent'),
        ),
    ]
