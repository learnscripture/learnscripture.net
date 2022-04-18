from django.db.models.signals import post_delete, post_save

from .models import Comment, delete_event_generated_for_comment
from .signals import new_comment


def comment_post_save_handler(sender, **kwargs):
    if kwargs.get("raw", False):
        return

    comment = kwargs["instance"]
    if kwargs["created"]:
        new_comment.send(sender=comment)


def comment_post_delete_handler(sender, **kwargs):
    comment = kwargs["instance"]
    assert comment.id is not None
    delete_event_generated_for_comment(comment.id)


post_save.connect(comment_post_save_handler, sender=Comment)
post_delete.connect(comment_post_delete_handler, sender=Comment)
