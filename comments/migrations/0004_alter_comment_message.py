# Generated by Django 3.2.9 on 2022-04-18 18:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comments", "0003_alter_comment_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="message",
            field=models.TextField(max_length=10000),
        ),
    ]
