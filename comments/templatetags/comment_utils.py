from django.template import Library

register = Library()

# Due to way comments are connected to Event, and the way that prefetched
# queries work, it is better to implement hellbanning filtering for comments
# in a template tag.

# This tag assumes that comments have been fetched with authors prefetched

@register.filter
def filter_comments(comments, viewer):
    if viewer is None or not viewer.is_hellbanned:
        return [c for c in comments
                if not c.author.is_hellbanned]
    else:
        return list(comments)
