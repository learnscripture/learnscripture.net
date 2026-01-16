from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("scores", "0002_scorelog_reference"),
    ]

    operations = [
        migrations.RenameModel("ScoreLog", "ActionLog"),
    ]
