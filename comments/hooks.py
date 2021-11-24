from django.db.models.signals import post_save

from .models import Comment
from .signals import new_comment


def comment_post_save_handler(sender, **kwargs):
    if kwargs.get("raw", False):
        return

    comment = kwargs["instance"]
    if kwargs["created"]:
        new_comment.send(sender=comment)


post_save.connect(comment_post_save_handler, sender=Comment)
