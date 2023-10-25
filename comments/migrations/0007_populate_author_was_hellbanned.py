# Generated by Django 4.1.7 on 2023-04-26 10:08

from django.db import migrations


def forwards(apps, _):
    try:
        ModerationAction = apps.get_model("moderation", "ModerationAction")
    except LookupError:
        return

    for action in ModerationAction.objects.filter(action_type="user_hellbanned"):
        comments = action.user.comments.all().filter(created__gt=action.done_at)
        if action.reversed_at:
            comments = comments.filter(created__lt=action.reversed_at)
        comments.update(author_was_hellbanned=True)


def backwards(apps, _):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("comments", "0006_comment_author_was_hellbanned"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
