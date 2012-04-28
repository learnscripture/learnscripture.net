from django.conf import settings
from django.core.urlresolvers import reverse
from django.dispatch import receiver

from awards.signals import new_award


@receiver(new_award)
def notify_about_new_award(sender, **kwargs):
    award = sender
    account = award.account
    account.identity.notices.create(message_html="""
<img src="%s%s"> You've earned a new badge: <a href="%s">%s</a>""" %
                                    (settings.STATIC_URL,
                                     award.image_small(),
                                     reverse('user_stats', args=(account.username,)),
                                     award.short_description())
                                    )

