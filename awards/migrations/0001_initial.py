import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Award",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                (
                    "award_type",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, "Student"),
                            (1, "Master"),
                            (2, "Sharer"),
                            (3, "Trend setter"),
                            (4, "Ace"),
                            (5, "Recruiter"),
                            (6, "Hacker"),
                            (7, "Weekly champion"),
                            (8, "Reigning weekly champion"),
                            (9, "Addict"),
                            (10, "Organizer"),
                            (11, "Consistent learner"),
                        ]
                    ),
                ),
                ("level", models.PositiveSmallIntegerField()),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "account",
                    models.ForeignKey(related_name="awards", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
