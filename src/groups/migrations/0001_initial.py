import autoslug.fields
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Group",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("name", models.CharField(max_length=255)),
                ("slug", autoslug.fields.AutoSlugField(populate_from="name", unique=True, editable=False)),
                ("description", models.TextField(blank=True)),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                ("public", models.BooleanField(default=False)),
                ("open", models.BooleanField(default=False)),
                (
                    "created_by",
                    models.ForeignKey(
                        related_name="groups_created", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Invitation",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                (
                    "account",
                    models.ForeignKey(
                        related_name="invitations", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        related_name="invitations_created", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
                ("group", models.ForeignKey(related_name="invitations", to="groups.Group", on_delete=models.CASCADE)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Membership",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "account",
                    models.ForeignKey(
                        related_name="memberships", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
                ("group", models.ForeignKey(related_name="memberships", to="groups.Group", on_delete=models.CASCADE)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="group",
            name="members",
            field=models.ManyToManyField(
                related_name="groups", through="groups.Membership", to=settings.AUTH_USER_MODEL
            ),
            preserve_default=True,
        ),
    ]
