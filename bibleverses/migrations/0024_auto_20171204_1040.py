# Generated by Django 1.11.6 on 2017-12-04 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0023_auto_20171024_1838"),
    ]

    operations = [
        migrations.AlterField(
            model_name="verseset",
            name="set_type",
            field=models.CharField(choices=[("SELECTION", "Selection"), ("PASSAGE", "Passage")], max_length=20),
        ),
    ]
