# Generated by Django 2.0.10 on 2019-06-27 09:10

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0002_populate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contentitem',
            name='template_name',
        ),
        migrations.AlterField(
            model_name='contentitem',
            name='metadata',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='contentitem',
            name='used_on_pages_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='used on pages'),
        ),
        migrations.AlterField(
            model_name='page',
            name='metadata',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='template_name',
            field=models.CharField(blank=True, choices=[('cms_singlecol.html', 'Single column')], max_length=70),
        ),
    ]
