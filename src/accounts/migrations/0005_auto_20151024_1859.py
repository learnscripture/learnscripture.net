from django.db import migrations, models

import accounts.models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_auto_20150502_0938"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="account",
            managers=[
                ("objects", accounts.models.AccountManager()),
            ],
        ),
        migrations.AlterField(
            model_name="account",
            name="email",
            field=models.EmailField(max_length=254),
        ),
        migrations.AlterField(
            model_name="account",
            name="last_login",
            field=models.DateTimeField(null=True, verbose_name="last login", blank=True),
        ),
    ]
