from django.db import models
from django.utils import timezone

from bibleverses.models import BibleVersion

from learnscripture.datastructures import make_choices


SubscriptionType = make_choices('SubscriptionType',
                                [(0, 'FREE_TRIAL', 'Free trial'),
                                 (1, 'PAID_UP', 'Paid up'),
                                 (2, 'EXPIRED', 'Expired'),
                                 (3, 'LIFETIME_FREE', 'Lifetime free')]
                                )

# Account is separate from Identity to allow guest users to use the site fully
# without signing up.
# Everything related to learning verses is related to Identity.
# Social aspects and payment aspects are related to Account.


class Account(models.Model):
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(default=timezone.now)
    date_joined = models.DateTimeField(default=timezone.now)
    subscription = models.PositiveSmallIntegerField(choices=SubscriptionType.choice_list)
    paid_until = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.email


class IdentityManager(models.Manager):
    def get_query_set(self):
        return super(IdentityManager, self).get_query_set().select_related('default_bible_version')


class Identity(models.Model):
    account = models.OneToOneField(Account, null=True, blank=True, default=None)
    date_created = models.DateTimeField(default=timezone.now)

    # Preferences
    default_bible_version = models.ForeignKey(BibleVersion, null=True, blank=True)

    objects = IdentityManager()

    class Meta:
        verbose_name_plural = 'identities'

    def __unicode__(self):
        if self.account_id is None:
            return '<Identity %s>' % self.id
        else:
            return '<Identity %s>' % self.account

    def add_verse_set(self, verse_set):
        """
        Adds the verses in a VerseSet to the users UserVerseStatus objects,
        and returns the UserVerseStatus objects.
        """
        out = []
        vc_ids = [vc.id for vc in verse_set.verse_choices.all()]
        uvcs = dict([(uvc.verse_choice_id, uvc) for uvc in self.verse_statuses.filter(verse_choice__in=vc_ids)])
        # Want to preserve order of verse_set
        for vc_id in vc_ids:
            uvc = uvcs.get(vc_id, None)
            # If the user already has this verse choice, we don't want to change
            # the version. Otherwise we set the version to the default
            if uvc is None:
                out.append(self.verse_statuses.create(verse_choice_id=vc_id,
                                                      version=self.default_bible_version))
            else:
                out.append(uvc)
        return out
