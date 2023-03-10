# Generated by Django 1.11.4 on 2017-10-18 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scores", "0006_auto_20170905_1403"),
    ]

    operations = [
        migrations.AlterField(
            model_name="actionlog",
            name="reason",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, "Verse tested"),
                    (1, "Verse reviewed"),
                    (2, "Review completed"),
                    (3, "Perfect!"),
                    (4, "Verse fully learned"),
                    (5, "Earned award"),
                ]
            ),
        ),
    ]
