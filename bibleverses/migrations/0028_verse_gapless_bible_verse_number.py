# Generated by Django 1.11.6 on 2018-01-04 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0027_auto_20171204_1143"),
    ]

    operations = [
        migrations.AddField(
            model_name="verse",
            name="gapless_bible_verse_number",
            field=models.PositiveIntegerField(null=True),
        ),
    ]
