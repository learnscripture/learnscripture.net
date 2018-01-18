from django.utils.html import format_html

from learnscripture.celery import app


@app.task(ignore_result=True)
def notify_account_about_comment(comment_id):
    from comments.models import Comment
    comment = Comment.objects.get(id=comment_id)

    event = comment.event

    if event is None:
        return

    # Notify the account that generated the event
    notify_about_comment(event, comment, event.account)
    # Notify contributors
    for c in event.comments.all():
        notify_about_comment(event, comment, c.author)


def notify_about_comment(event, comment, account):

    # Don't notify comment author about own comment
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

    if account == event.account:
        msg = format_html('You have new comments on <b><a href="{0}">your event</a></b> "{1}"',
                          event.get_absolute_url(),
                          event.render_html(account.default_language_code)
                          )
    else:
        msg = format_html('There are <b><a href="{0}">new comments</a></b> on the event "{1}"',
                          event.get_absolute_url(),
                          event.render_html(account.default_language_code)
                          )

    notice = account.add_html_notice(msg)
    notice.related_event = event
    notice.save()
