# Generated by Django 1.11.6 on 2017-12-09 08:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0007_auto_20171208_0713"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="event",
            name="message_html",
        ),
    ]
