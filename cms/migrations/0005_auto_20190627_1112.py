# Generated by Django 2.0.10 on 2019-06-27 11:12

from django.db import migrations


def forwards(apps, schema_editor):
    Page = apps.get_model('cms', 'Page')
    Page.objects.filter(template_name='fiber_singlecol.html').update(template_name='cms_singlecol.html')


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0004_auto_20190627_1037'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]