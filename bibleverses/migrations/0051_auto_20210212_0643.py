# Generated by Django 3.1.6 on 2021-02-12 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0050_auto_20200724_0545"),
    ]

    operations = [
        migrations.AlterField(
            model_name="wordsuggestiondata",
            name="suggestions",
            field=models.JSONField(default=list),
        ),
    ]
