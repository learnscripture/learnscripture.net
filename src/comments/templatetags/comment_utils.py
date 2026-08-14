from django.template import Library

from accounts.models import Account
from comments.models import Comment

register = Library()

# Due to way comments are connected to Event, and the way that prefetched
# queries work, it is better to implement filtering and moderation filtering for
# comments in a template tag.

# This tag assumes that comments have been fetched with authors prefetched


@register.filter
def filter_comments(comments: list[Comment], viewer: Account):
    return [c for c in comments if c.is_visible_for_account(viewer)]
