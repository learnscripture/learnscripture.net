from app_metrics.utils import metric

from accounts.signals import new_account


def new_account_callback(sender, **kwargs):
    metric('new_account')
    account = sender
    referrer_id = account.identity.referred_by_id
    if referrer_id is not None:
        import awards.tasks
        awards.tasks.give_recruiter_award.apply_async([referrer_id], countdown=5)

    import events.tasks
    events.tasks.create_new_account_event.apply_async([account.id], countdown=5)

new_account.connect(new_account_callback)
