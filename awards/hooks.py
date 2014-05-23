from django.conf import settings
from django.core.urlresolvers import reverse
from django.dispatch import receiver
from django.utils.html import format_html

from accounts.signals import new_account, verse_tested, scored_100_percent
from awards.signals import new_award, lost_award
import awards.tasks
from bibleverses.signals import verse_set_chosen, public_verse_set_created
from groups.signals import group_joined


@receiver(new_award)
def notify_about_new_award(sender, **kwargs):
    award = sender
    account = award.account
    if award.level > 1:
        template = """<img src="{0}{1}"> You've levelled up on one of your badges: <a href="{2}">{3}</a>."""
    else:
        template = """<img src="{0}{1}"> You've earned a new badge: <a href="{2}">{3}</a>."""

    award_url = reverse('user_stats', args=(account.username,))

    msg = format_html(template,
                      settings.STATIC_URL,
                      award.image_small(),
                      award_url,
                      award.short_description())
    if 'points' in kwargs:
        points = kwargs['points']
        if points > 0:
            msg = msg + format_html(' Points bonus: {0}.', points)

    # Facebook: this notice could be displayed on any page, and we want the
    # 'redirect_uri' parameter to take them back to where they were.  So we
    # render the link to facebook using javascript, embedding necessary data
    # using data attributes.
    msg = msg + format_html('<span class="broadcast"'
                            ' data-link="{0}"'
                            ' data-picture="{1}{2}"'
                            ' data-award-id="{3}"'
                            ' data-award-level="{4}"'
                            ' data-award-name="{5}"'
                            ' data-account-username="{6}"'
                            '></span>',
                            award_url,
                            settings.STATIC_URL,
                            award.image_medium(),
                            award.id, # not needed at the moment
                            award.level,
                            award.short_description(),
                            account.username,
                            )

    account.identity.add_html_notice(msg)


@receiver(lost_award)
def notify_about_lost_award(sender, **kwargs):
    award = sender
    account = award.account
    msg = """<img src="%s%s"> You've lost <a href="%s">%s</a>."""

    msg = msg % (settings.STATIC_URL,
                 award.image_small(),
                 reverse('award', args=(award.award_detail.slug(),)),
                 award.short_description())

    account.identity.add_html_notice(msg)


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


@receiver(scored_100_percent)
def scored_100_percent_receiver(sender, **kwargs):
    account = sender
    awards.tasks.give_ace_awards.apply_async([account.id],
                                             countdown=2)


@receiver(group_joined)
def group_joined_receiver(sender, **kwargs):
    group = sender
    awards.tasks.give_organizer_awards.apply_async([group.created_by_id],
                                                   countdown=2)
