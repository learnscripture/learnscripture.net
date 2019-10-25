# Generated by Django 2.2.4 on 2019-10-25 05:20

import functools
import operator

from django.db import migrations, models

# Correct passage VerseSets that are missing VerseChoices
# due to some Bible versions having missing verses.

# Affected books are:
BOOKS = {'BOOK39', 'BOOK40', 'BOOK41', 'BOOK42', 'BOOK43', 'BOOK44', 'BOOK46'}


def forwards(apps, schema_editor):
    # Need to use parsing tools, so do project imports
    from bibleverses.models import VerseSet, VerseSetType
    from bibleverses.parsing import parse_validated_internal_reference
    from learnscripture.utils.iterators import iter_chunked_queryset

    verse_sets = VerseSet.objects.filter(
        set_type=VerseSetType.PASSAGE,
    ).filter(
        functools.reduce(operator.or_, [models.Q(passage_id__startswith=b + ' ') for b in BOOKS]),
    ).prefetch_related('verse_choices')
    for vs in iter_chunked_queryset(verse_sets, 30):
        refs = parse_validated_internal_reference(vs.passage_id).to_list()
        if len(refs) != len(vs.verse_choices.all()):
            print("Fixing " + repr(vs))
            internal_reference_list = [ref.canonical_form() for ref in parse_validated_internal_reference(vs.passage_id).to_list()]
            vs.set_verse_choices(internal_reference_list)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0044_populate_any_language'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
