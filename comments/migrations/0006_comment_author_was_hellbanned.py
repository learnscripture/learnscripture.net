# Generated by Django 4.1.7 on 2023-04-26 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comments", "0005_alter_comment_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="author_was_hellbanned",
            field=models.BooleanField(default=False),
        ),
    ]
