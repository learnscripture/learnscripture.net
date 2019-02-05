# Generated by Django 2.0.10 on 2019-02-05 17:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0037_auto_20190205_1706'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE bibleverses_wordsuggestiondata ALTER COLUMN suggestions TYPE jsonb USING suggestions::text::jsonb;"
            "", hints={'target_dbs': ['wordsuggestions']})
    ]