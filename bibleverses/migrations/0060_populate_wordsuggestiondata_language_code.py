# Generated by Django 3.2.9 on 2023-02-11 18:00

from django.db import migrations


def forwards(apps, schema_editor):
    WordSuggestionData = apps.get_model("bibleverses", "WordSuggestionData")
    WordSuggestionData.objects.filter(version_slug="RVG").update(language_code="es")
    WordSuggestionData.objects.filter(version_slug="").update(language_code="en")


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0059_wordsuggestiondata_language_code"),
    ]

    operations = [
        migrations.RunPython(
            forwards,
            backwards,
            hints={"target_dbs": ["wordsuggestions"]},
        ),
    ]