# Generated by Django 2.0.10 on 2019-06-29 12:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0006_auto_20190629_1148"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="contentitem",
            name="used_on_pages_data",
        ),
    ]
