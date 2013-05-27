from celery.task import task
from django.utils.html import format_html

@task(ignore_result=True)
def notify_account_about_comment(comment_id):
    from comments.models import Comment
    comment = Comment.objects.get(id=comment_id)

    event = comment.event

    if event is None:
        return

    # Notify the account that generated the event
    account = event.account

    # But not if it is the author:
    if account == comment.author:
        return

    # And not if commenter is hellbanned:
    if comment.author.is_hellbanned and not account.is_hellbanned:
        return

    # And not if they already have a notice about it.
    if account.identity.notices.filter(
        related_event=event,
        ).exists():
        return

    msg = format_html('You have new comments on <b><a href="{0}">your event</a></b> "{1}"',
                      event.get_absolute_url(),
                      event.render_html()
                      )

    notice = account.add_html_notice(msg)
    notice.related_event = event
    notice.save()

