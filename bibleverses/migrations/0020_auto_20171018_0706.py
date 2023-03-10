# Generated by Django 1.11.4 on 2017-10-18 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0019_auto_20171018_0705"),
    ]

    operations = [
        migrations.AlterField(
            model_name="versechoice",
            name="internal_reference",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name="versechoice",
            unique_together={("verse_set", "internal_reference")},
        ),
    ]
