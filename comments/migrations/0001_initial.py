import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("groups", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                ("message", models.TextField()),
                ("hidden", models.BooleanField(default=False)),
                (
                    "author",
                    models.ForeignKey(related_name="comments", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
                ),
                (
                    "event",
                    models.ForeignKey(
                        related_name="comments", blank=True, to="events.Event", null=True, on_delete=models.CASCADE
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        related_name="comments", blank=True, to="groups.Group", null=True, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
