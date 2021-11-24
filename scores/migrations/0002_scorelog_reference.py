from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scores", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="scorelog",
            name="reference",
            field=models.CharField(max_length=255, blank=True),
            preserve_default=True,
        ),
    ]
