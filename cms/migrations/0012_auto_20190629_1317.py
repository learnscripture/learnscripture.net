# Generated by Django 2.0.10 on 2019-06-29 13:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0011_auto_20190629_1255'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contentitem',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='page',
            name='metadata',
        ),
    ]