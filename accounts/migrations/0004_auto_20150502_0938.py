from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_identity_enable_vibration"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="email_bounced",
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="identity",
            name="enable_vibration",
            field=models.BooleanField(default=True, verbose_name="Vibrate on mistakes"),
            preserve_default=True,
        ),
    ]
