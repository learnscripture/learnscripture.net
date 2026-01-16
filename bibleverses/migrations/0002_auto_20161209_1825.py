from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("bibleverses", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="verse",
            old_name="text",
            new_name="text_saved",
        ),
    ]
