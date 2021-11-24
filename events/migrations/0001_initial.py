import django.contrib.postgres.fields
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("message_html", models.TextField()),
                (
                    "event_type",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "General"),
                            (2, "New account"),
                            (3, "Award received"),
                            (4, "Points milestone"),
                            (5, "Verses started milestone"),
                            (6, "Verses finished milestone"),
                            (7, "Verse set created"),
                            (8, "Started learning a verse set"),
                            (9, "Award lost"),
                            (10, "Group joined"),
                            (11, "Group created"),
                            (12, "Started learning catechism"),
                            (13, "New comment"),
                        ]
                    ),
                ),
                ("weight", models.PositiveSmallIntegerField(default=10)),
                ("event_data", django.contrib.postgres.fields.JSONField(default=dict, blank=True)),
                ("created", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("url", models.CharField(max_length=255, blank=True)),
                ("account", models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ("parent_event", models.ForeignKey(blank=True, to="events.Event", null=True, on_delete=models.CASCADE)),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
