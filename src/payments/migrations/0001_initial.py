from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ipn", "0003_auto_20141117_1647"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DonationDrive",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("start", models.DateTimeField()),
                ("finish", models.DateTimeField()),
                ("active", models.BooleanField(default=False)),
                ("message_html", models.TextField()),
                (
                    "hide_if_donated_days",
                    models.PositiveIntegerField(
                        help_text="The donation drive will be hidden for users who have donated within this number of days"
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("amount", models.DecimalField(max_digits=10, decimal_places=2)),
                ("created", models.DateTimeField()),
                (
                    "account",
                    models.ForeignKey(related_name="payments", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
                ),
                ("paypal_ipn", models.ForeignKey(to="ipn.PayPalIPN", on_delete=models.CASCADE)),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
