# Generated by Django 3.2.9 on 2021-11-25 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("learnscripture", "0002_sitenotice_language_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitenotice",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
    ]