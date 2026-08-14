import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(default=django.utils.timezone.now, verbose_name="last login")),
                ("username", models.CharField(unique=True, max_length=100)),
                ("first_name", models.CharField(max_length=100, blank=True)),
                ("last_name", models.CharField(max_length=100, blank=True)),
                ("email", models.EmailField(max_length=75)),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now)),
                ("is_tester", models.BooleanField(default=False)),
                ("is_moderator", models.BooleanField(default=False)),
                ("is_under_13", models.BooleanField(default=False, verbose_name="Under 13 years old")),
                ("is_active", models.BooleanField(default=True)),
                ("enable_commenting", models.BooleanField(default=True, verbose_name="Enable comment system")),
                ("is_hellbanned", models.BooleanField(default=False)),
                ("has_installed_android_app", models.BooleanField(default=False)),
                (
                    "remind_after",
                    models.PositiveSmallIntegerField(default=2, verbose_name="Send email reminders after (days)"),
                ),
                (
                    "remind_every",
                    models.PositiveSmallIntegerField(default=3, verbose_name="Send email reminders every (days)"),
                ),
                ("last_reminder_sent", models.DateTimeField(null=True, blank=True)),
                ("is_superuser", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["username"],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Identity",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("date_created", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "desktop_testing_method",
                    models.PositiveSmallIntegerField(
                        default=0,
                        choices=[
                            (0, "Full words - recommended for full keyboards and normal typing skills"),
                            (1, "First letter - recommended for slower typers"),
                            (2, "On screen buttons - recommended for handheld devices"),
                        ],
                    ),
                ),
                (
                    "touchscreen_testing_method",
                    models.PositiveSmallIntegerField(
                        default=2,
                        choices=[
                            (0, "Full words - recommended for full keyboards and normal typing skills"),
                            (1, "First letter - recommended for slower typers"),
                            (2, "On screen buttons - recommended for handheld devices"),
                        ],
                    ),
                ),
                ("enable_animations", models.BooleanField(default=True)),
                ("enable_sounds", models.BooleanField(default=False)),
                (
                    "interface_theme",
                    models.CharField(
                        default="calm",
                        max_length=30,
                        choices=[
                            ("calm", "Slate"),
                            ("bubblegum", "Bubblegum pink"),
                            ("bubblegum2", "Bubblegum green"),
                            ("space", "Space"),
                        ],
                    ),
                ),
                ("track_learning", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name_plural": "identities",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Notice",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("message_html", models.TextField()),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                ("seen", models.DateTimeField(default=None, null=True, blank=True)),
                (
                    "for_identity",
                    models.ForeignKey(related_name="notices", to="accounts.Identity", on_delete=models.CASCADE),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
