from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0002_donationdrive_target"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="paypal_ipn",
            field=models.ForeignKey(related_name="payments", to="ipn.PayPalIPN", on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
