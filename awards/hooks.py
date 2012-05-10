from django.conf import settings
from django.core.urlresolvers import reverse
from django.dispatch import receiver

from accounts.signals import new_account, verse_tested
from awards.signals import new_award, lost_award
import awards.tasks
from bibleverses.signals import verse_set_chosen, public_verse_set_created


@receiver(new_award)
def notify_about_new_award(sender, **kwargs):
    award = sender
    account = award.account
    if award.level > 1:
        msg = """<img src="%s%s"> You've levelled up on one of your badges: <a href="%s">%s</a>."""
    else:
        msg = """<img src="%s%s"> You've earned a new badge: <a href="%s">%s</a>."""

    msg = msg % (settings.STATIC_URL,
                 award.image_small(),
                 reverse('user_stats', args=(account.username,)),
                 award.short_description())
    if 'points' in kwargs:
        points = kwargs['points']
        if points > 0:
            msg = msg + ' Points bonus: %d' % points

    account.identity.notices.create(message_html=msg)


@receiver(lost_award)
def notify_about_lost_award(sender, **kwargs):
    award = sender
    account = award.account
    msg = """<img src="%s%s"> You've lost <a href="%s">%s</a>."""

    msg = msg % (settings.STATIC_URL,
                 award.image_small(),
                 reverse('award', args=(award.award_detail.slug(),)),
                 award.short_description())

    account.identity.notices.create(message_html=msg)


@receiver(verse_set_chosen)
def verse_set_chosen_receiver(sender, **kwargs):
    verse_set = sender
    awards.tasks.give_verse_set_used_awards.delay(verse_set.created_by_id)


@receiver(new_account)
def new_account_receiver(sender, **kwargs):
    account = sender
    referrer_id = account.identity.referred_by_id
    if referrer_id is not None:
        awards.tasks.give_recruiter_award.apply_async([referrer_id], countdown=5)


@receiver(verse_tested)
def verse_tested_receiver(sender, **kwargs):
    identity = sender
    # Delay to allow this request's transaction to finish count to be updated.
    awards.tasks.give_learning_awards.apply_async([identity.account_id],
                                                  countdown=2)


@receiver(public_verse_set_created)
def public_verse_set_created_receiver(sender, **kwargs):
    verse_set = sender
    awards.tasks.give_sharer_awards.apply_async([verse_set.created_by_id],
                                               countdown=2)
