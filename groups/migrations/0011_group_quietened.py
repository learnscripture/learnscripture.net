# Generated by Django 4.1.7 on 2023-04-21 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("groups", "0010_alter_group_language_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="group",
            name="quietened",
            field=models.BooleanField(default=False, help_text="A quietened group will be less visible on news feeds"),
        ),
    ]