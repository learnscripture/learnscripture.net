from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_auto_20160204_0925"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="identity",
            name="track_learning",
        ),
    ]
