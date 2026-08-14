from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("scores", "0003_auto_20160204_0954"),
    ]

    operations = [
        migrations.AlterField(
            model_name="actionlog",
            name="account",
            field=models.ForeignKey(related_name="action_logs", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
    ]
