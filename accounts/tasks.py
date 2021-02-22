import django_ftl

from learnscripture.ftl_bundles import t
from learnscripture.utils.tasks import task


@task
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

    with django_ftl.override(account.default_language_code):
        if account == event.account:
            msg = t('events-you-have-new-comments-notification-html',
                    dict(event_url=event.get_absolute_url(),
                         event=event.render_html(account.default_language_code)))
        else:
            msg = t('events-new-comments-notification-html',
                    dict(event_url=event.get_absolute_url(),
                         event=event.render_html(account.default_language_code)))

    notice = account.add_html_notice(msg)
    notice.related_event = event
    notice.save()
