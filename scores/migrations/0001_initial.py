from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ScoreLog",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("points", models.PositiveIntegerField()),
                (
                    "reason",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, b"Verse tested"),
                            (1, b"Verse revised"),
                            (2, b"Review completed"),
                            (3, b"Perfect!"),
                            (4, b"Verse fully learned"),
                            (5, b"Earned award"),
                        ]
                    ),
                ),
                ("accuracy", models.FloatField(null=True, blank=True)),
                ("created", models.DateTimeField()),
                (
                    "account",
                    models.ForeignKey(related_name="score_logs", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
                ),
            ],
            options={
                "ordering": ("-created",),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TotalScore",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("points", models.PositiveIntegerField(default=0)),
                ("visible", models.BooleanField(default=True)),
                (
                    "account",
                    models.OneToOneField(
                        related_name="total_score", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
