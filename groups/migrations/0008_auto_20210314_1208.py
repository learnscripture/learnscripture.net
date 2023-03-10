# Generated by Django 3.1.6 on 2021-03-14 12:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("groups", "0007_auto_20190629_1201"),
    ]

    operations = [
        migrations.AlterField(
            model_name="group",
            name="created_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, related_name="groups_created", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name="invitation",
            name="created_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="invitations_created",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
