# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import json_field.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HttpLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('response_data', models.TextField()),
                ('request_data', json_field.fields.JSONField(default='null', help_text='Enter a valid JSON object')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TrackingSnapshot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_path', models.CharField(max_length=255)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('snapshot_type', models.CharField(max_length=20, choices=[(b'insert', b'Insert'), (b'update', b'Update'), (b'delete', b'Delete')])),
                ('applied', models.BooleanField(default=False)),
                ('old_fields', json_field.fields.JSONField(default='null', help_text='Enter a valid JSON object')),
                ('new_fields', json_field.fields.JSONField(default='null', help_text='Enter a valid JSON object')),
            ],
            options={
                'ordering': ['created'],
            },
            bases=(models.Model,),
        ),
    ]
