# Generated by Django 2.2.4 on 2019-08-12 07:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0020_remove_contentitem_content_html"),
    ]

    operations = [
        migrations.AlterField(
            model_name="page",
            name="level",
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name="page",
            name="lft",
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name="page",
            name="rght",
            field=models.PositiveIntegerField(editable=False),
        ),
    ]
