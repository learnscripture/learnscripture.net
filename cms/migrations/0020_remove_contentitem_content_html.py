# Generated by Django 2.0.10 on 2019-06-30 15:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0019_populate_content'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contentitem',
            name='content_html',
        ),
    ]
