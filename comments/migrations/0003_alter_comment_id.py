# Generated by Django 3.2.9 on 2021-11-25 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comments", "0002_auto_20190801_1952"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
    ]