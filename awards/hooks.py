import django_ftl
from django.conf import settings
from django.dispatch import receiver
from django.urls import reverse
from django.utils.html import format_html

import awards.tasks
from accounts.signals import new_account, scored_100_percent, verse_tested
from awards.signals import new_award
from bibleverses.signals import public_verse_set_created, verse_set_chosen
from common.utils.html import link
from groups.signals import group_joined
from learnscripture.ftl_bundles import t


@receiver(new_award)
def notify_about_new_award(sender, **kwargs):
    award = sender
    account = award.account
    with django_ftl.override(account.default_language_code):
        msg_html = new_award_msg_html(award, account, points=kwargs.get('points', None))
        account.identity.add_html_notice(msg_html)


def new_award_msg_html(award, account, points=None):
    img_html = format_html(
        '<img src="{0}{1}">',
        settings.STATIC_URL,
        award.image_small(),
    )
    award_url = reverse('user_stats', args=(account.username,))
    award_link = link(award_url, award.short_description())

    if award.level > 1:
        msg = t('awards-levelled-up-html', dict(award=award_link))
    else:
        msg = t('awards-new-award-html', dict(award=award_link))

    if points is not None and points > 0:
        points_msg = t('awards-points-bonus', dict(points=points))
        msg = format_html("{0} {1}", msg, points_msg)

    # Facebook: this notice could be displayed on any page, and we want the
    # 'redirect_uri' parameter to take them back to where they were.  So we
    # render the link to facebook using javascript, embedding necessary data
    # using data attributes.
    tell_people_link = t('awards-tell-people-html',
                         dict(facebook=format_html('<a data-facebook-link><i class="icon-facebook"></i> Facebook</a>'),
                              twitter=format_html('<a data-twitter-link><i class="icon-twitter"></i> Twitter</a>'),
                              ))

    caption = t('awards-social-media-default-message',
                dict(award=award.short_description()))

    tell_people_wrapper = format_html(
        '<span class="broadcast"'
        ' data-link="{0}"'
        ' data-picture="{1}{2}"'
        ' data-award-id="{3}"'
        ' data-award-level="{4}"'
        ' data-award-name="{5}"'
        ' data-account-username="{6}"'
        ' data-caption="{7}"'
        '>{8}</span>',
        award_url,
        settings.STATIC_URL,
        award.image_medium(),
        award.id,  # not needed at the moment
        award.level,
        award.short_description(),
        account.username,
        caption,
        tell_people_link
    )
    return format_html('{0} {1} {2}', img_html, msg, tell_people_wrapper)


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
