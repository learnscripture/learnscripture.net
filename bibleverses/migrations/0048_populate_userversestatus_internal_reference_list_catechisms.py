# Generated by Django 2.2.4 on 2020-06-10 07:16

from django.db import migrations


def forwards(app_configs, schema_editor):
    from bibleverses.models import TextType
    from learnscripture.utils.iterators import chunked_queryset
    UserVerseStatus = app_configs.get_model('bibleverses', 'UserVerseStatus')

    # Copied logic from Identity.create_verse_status
    uvs_query = (UserVerseStatus
                 .objects
                 .filter(version__text_type=TextType.CATECHISM)
                 .select_related('version')
                 )
    for i, batch in enumerate(chunked_queryset(uvs_query, 1000)):
        print(f'{i * 1000} items done')
        to_update = []
        for uvs in batch:
            uvs.internal_reference_list = [uvs.localized_reference]
            to_update.append(uvs)
        UserVerseStatus.objects.bulk_update(to_update, ['internal_reference_list'])


def backwards(app_configs, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0047_populate_userversestatus_internal_reference_list'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]