# Generated by Django 1.11.6 on 2018-01-18 09:31

from django.db import migrations


def forwards(apps, schema_editor):
    Event = apps.get_model("events.Event")
    VerseSet = apps.get_model("bibleverses.VerseSet")
    for event in Event.objects.filter(event_type__in=["VERSE_SET_CREATED", "STARTED_LEARNING_VERSE_SET"]):
        vs_id = event.event_data["verse_set_id"]
        verse_set = VerseSet.objects.get(id=vs_id)
        event.event_data["verse_set_language_code"] = verse_set.language_code
        event.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0008_remove_event_message_html"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
