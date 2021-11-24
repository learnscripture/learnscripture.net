from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_auto_20151024_1859"),
    ]

    operations = [
        migrations.AlterField(
            model_name="identity",
            name="track_learning",
            field=models.BooleanField(
                default=False,
                help_text="Set this to enable detailed tracking of a user's learning, for debugging purposes.",
            ),
        ),
    ]
