# Generated by Django 1.11.4 on 2017-09-24 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0009_auto_20170905_1403"),
    ]

    operations = [
        migrations.AlterField(
            model_name="textversion",
            name="language_code",
            field=models.CharField(choices=[("en", "English"), ("tr", "Türkçe")], default="en", max_length=2),
        ),
    ]
