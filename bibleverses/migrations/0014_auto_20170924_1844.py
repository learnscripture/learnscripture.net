# Generated by Django 1.11.4 on 2017-09-24 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0013_auto_20170924_1840"),
    ]

    operations = [
        migrations.AlterField(
            model_name="verse",
            name="last_verse_number",
            field=models.PositiveSmallIntegerField(),
        ),
    ]
