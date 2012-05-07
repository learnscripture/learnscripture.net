from django.conf import settings
from django.core.urlresolvers import reverse
from django.dispatch import receiver

from awards.signals import new_award
from bibleverses.signals import verse_set_chosen


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


@receiver(verse_set_chosen)
def verse_set_chosen_receiver(sender, **kwargs):
    verse_set = sender
    from awards.tasks import give_verse_set_used_awards
    give_verse_set_used_awards.delay(verse_set.created_by_id)

