# Generated by Django 2.0.10 on 2019-06-29 12:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0007_remove_contentitem_used_on_pages_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='show_in_menu',
        ),
    ]