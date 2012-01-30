from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password

from bibleverses.models import BibleVersion, MemoryStage, StageType, BibleVersion, VerseChoice, VerseSet, VerseSetType

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
    username = models.CharField(max_length=100, blank=False)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(default=timezone.now)
    date_joined = models.DateTimeField(default=timezone.now)
    subscription = models.PositiveSmallIntegerField(choices=SubscriptionType.choice_list)
    paid_until = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw_password):
            self.set_password(raw_password)
            self.save()
        return check_password(raw_password, self.password, setter)

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

    @property
    def expires_on(self):
        from django.conf import settings
        return self.date_created + timedelta(settings.IDENTITY_EXPIRES_DAYS)

    @property
    def expired(self):
        return self.account_id is None and self.expires_on < timezone.now()

    class Meta:
        verbose_name_plural = 'identities'

    def __unicode__(self):
        if self.account_id is None:
            return '<Identity %s>' % self.id
        else:
            return '<Identity %s>' % self.account

    def __repr__(self):
        return unicode(self)

    def add_verse_set(self, verse_set):
        """
        Adds the verses in a VerseSet to the user's UserVerseStatus objects,
        and returns the UserVerseStatus objects.
        """
        out = []
        vcs = list(verse_set.verse_choices.all())
        vc_ids = [vc.id for vc in vcs]

        uvss = set(self.verse_statuses.filter(verse_choice__in=vc_ids, ignored=False))
        uvss_dict = dict([(uvs.verse_choice_id, uvs) for uvs in uvss])

        # Want to preserve order of verse_set, so iterate like this:
        for vc in vcs:
            if vc.id in uvss_dict:
                # If the user already has this verse choice, we don't want to change
                # the version, so use the existing UVS.
                out.append(uvss_dict[vc.id])
            else:
                # Otherwise we set the version to the default
                new_uvs = self.create_verse_status(vc, self.default_bible_version)
                new_uvs.ignored = False
                new_uvs.save()

                out.append(new_uvs)
        return out

    def record_verse_action(self, reference, version_slug, stage_type, accuracy):
        s = self.verse_statuses.filter(verse_choice__reference=reference,
                                       version__slug=version_slug)
        mem_stage = {
            StageType.READ: MemoryStage.SEEN,
            StageType.TEST_TYPE_FULL: MemoryStage.TESTED,
            StageType.TEST_TYPE_QUICK: MemoryStage.TESTED,
            }[stage_type]

        s.filter(memory_stage__lt=mem_stage).update(memory_stage=mem_stage)

    def change_version(self, reference, version_slug, verse_set_id):
        """
        Changes the version used for a choice in a certain verse set.
        """
        # Note:
        # 1) If someone has memorised a verse in one version, it doesn't mean
        # they have it memorised in another version.
        # So changing versions implies creating a new UserVerseStatus.
        # However, if they change back again, we don't want to lose the history.
        # Therefore we have a 'disabled' flag to track which version is the
        # one they want.

        # 2) If they change the version for a verse that is part of a passage,
        # they will want to change it for the others in that passage too,
        # but may want to leave alone the UserVerseStatus for VerseChoices
        # that belong to other sets.

        # 3) A user can have more than one UserVerseStatus for the same
        # verse. If these are not in 'passage' type sets, we want them all
        # to be updated.

        verse_set = VerseSet.objects.get(id=verse_set_id)

        if verse_set.set_type == VerseSetType.PASSAGE:
            pass # TODO

        else:
            # Same reference
            old = self.verse_statuses.filter(verse_choice__reference=reference)
            # Not in 'passage' types
            old = old.exclude(verse_choice__verse_set__set_type=VerseSetType.PASSAGE)
            # Other versions
            old = old.exclude(version__slug=version_slug)

            old.update(ignored=True)

            # Find the UserVerseStatus with correct bible version
            correct = self.verse_statuses.filter(verse_choice__reference=reference)
            correct = correct.exclude(verse_choice__verse_set__set_type=VerseSetType.PASSAGE)

            correct = correct.filter(version__slug=version_slug)

            # For each VerseChoice, we need to create a new UserVerseStatus if
            # one with new version doesn't exist, or update 'ignored' if it
            # does.
            correct_l = list(correct.select_related('verse_choice'))
            correct.update(ignored=False)

            # Now we need to see if we need to create any new UserVerseStatuses.
            verse_choices = VerseChoice.objects.filter(reference=reference)
            verse_choices = list(verse_choices.exclude(verse_set__set_type=VerseSetType.PASSAGE))

            missing = set(verse_choices) - set([vs.verse_choice for vs in correct_l])
            if missing:
                version = BibleVersion.objects.get(slug=version_slug)
                for verse_choice in missing:
                    self.create_verse_status(verse_choice=verse_choice,
                                             version=version)

    def create_verse_status(self, verse_choice, version):
        uvs, new = self.verse_statuses.get_or_create(verse_choice=verse_choice,
                                                     version=version)

        same_verse = self.verse_statuses.filter(verse_choice__reference=verse_choice.reference,
                                                version=version).exclude(id=uvs.id)
        if same_verse and new:
            # Use existing data:
            same_verse = same_verse[0]
            uvs.memory_stage = same_verse.memory_stage
            uvs.strength = same_verse.strength
            uvs.first_seen = same_verse.first_seen
            uvs.last_seen = same_verse.last_seen

        return uvs
