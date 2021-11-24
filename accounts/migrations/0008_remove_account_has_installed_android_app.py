from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_remove_identity_track_learning"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="account",
            name="has_installed_android_app",
        ),
    ]
