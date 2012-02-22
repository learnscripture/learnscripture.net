from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password

from accounts import memorymodel
from bibleverses.models import BibleVersion, MemoryStage, StageType, BibleVersion, VerseChoice, VerseSet, VerseSetType

from learnscripture.datastructures import make_choices


SubscriptionType = make_choices('SubscriptionType',
                                [(0, 'FREE_TRIAL', 'Free trial'),
                                 (1, 'PAID_UP', 'Paid up'),
                                 (2, 'EXPIRED', 'Expired'),
                                 (3, 'LIFETIME_FREE', 'Lifetime free')]
                                )

TestingMethod = make_choices('TestingMethod',
                             [(0, 'FULL_WORDS', 'Full words - recommended for full keyboards and normal typing skills'),
                              (1, 'FIRST_LETTER', 'First letter - recommended for handheld devices and slower typers')]
                             )

THEMES = [('calm', 'Slate'),
          ('bubblegum', 'Bubblegum pink'),
          ('bubblegum2', 'Bubblegum green'),
          ]

# Account is separate from Identity to allow guest users to use the site fully
# without signing up.
# Everything related to learning verses is related to Identity.
# Social aspects and payment aspects are related to Account.


class Account(models.Model):
    username = models.CharField(max_length=100, blank=False, unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(default=timezone.now)
    date_joined = models.DateTimeField(default=timezone.now)
    subscription = models.PositiveSmallIntegerField(choices=SubscriptionType.choice_list,
                                                    default=SubscriptionType.FREE_TRIAL)
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
        return super(IdentityManager, self).get_query_set().select_related('default_bible_version', 'account')


# Most of business logic regarding verses is tied to Identity, for the sake of
# having somewhere to put it, and because most queries need to start
# 'identity.verse_statuses' so this may as well be 'self.verse_statuses'


class Identity(models.Model):
    account = models.OneToOneField(Account, null=True, blank=True, default=None)
    date_created = models.DateTimeField(default=timezone.now)

    # Preferences
    default_bible_version = models.ForeignKey(BibleVersion, null=True, blank=True,
                                              limit_choices_to={'public':True})
    testing_method = models.PositiveSmallIntegerField(choices=TestingMethod.choice_list,
                                                      null=True, default=None)
    enable_animations = models.BooleanField(blank=True, default=False)
    interface_theme = models.CharField(max_length=30, choices=THEMES,
                                       default='calm')

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

    @property
    def preferences_setup(self):
        return self.default_bible_version is not None and self.testing_method is not None


    def add_verse_set(self, verse_set, version=None):
        """
        Adds the verses in a VerseSet to the user's UserVerseStatus objects,
        and returns the UserVerseStatus objects.
        """
        if version is None:
            version = self.default_bible_version

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
                # Otherwise we set the version to the chosen one
                new_uvs = self.create_verse_status(vc, version)
                new_uvs.ignored = False
                new_uvs.save()

                out.append(new_uvs)
        return out

    def add_verse_choice(self, verse_choice, version=None):
        if version is None:
            version = self.default_bible_version

        existing = list(self.verse_statuses.filter(verse_choice=verse_choice, ignored=False))
        if existing:
            return existing[0]
        else:
            return self.create_verse_status(verse_choice, version)

    def record_verse_action(self, reference, version_slug, stage_type, accuracy=None):
        s = self.verse_statuses.filter(verse_choice__reference=reference,
                                       version__slug=version_slug)
        mem_stage = {
            StageType.READ: MemoryStage.SEEN,
            StageType.TEST: MemoryStage.TESTED,
            }[stage_type]

        # It's possible that they have already been tested, so don't move them
        # down to MemoryStage.SEEN
        s.filter(memory_stage__lt=mem_stage).update(memory_stage=mem_stage)

        now = timezone.now()
        if mem_stage == MemoryStage.TESTED:
            s0 = s[0] # Any should do, they should be all the same
            old_strength = s0.strength
            if s0.last_tested is None:
                time_elapsed = None
            else:
                time_elapsed = (now - s0.last_tested).total_seconds()
            new_strength = memorymodel.strength_estimate(old_strength, accuracy, time_elapsed)
            s.update(strength=new_strength,
                     last_tested=now)

        if mem_stage == MemoryStage.SEEN:
            s.filter(first_seen__isnull=True).update(first_seen=now)

    def change_version(self, reference, version_slug, verse_set_id):
        """
        Changes the version used for a choice in a certain verse set.
        """
        # Note:
        # 1) If someone has memorised a verse in one version, it doesn't mean
        # they have it memorised in another version.
        # So changing versions implies creating a new UserVerseStatus.
        # However, if they change back again, we don't want to lose the history.
        # Therefore we have an 'ignored' flag to track which version is the
        # one they want.

        # 2) If they change the version for a verse that is part of a passage,
        # they will want to change it for the others in that passage too,
        # but may want to leave alone the UserVerseStatus for VerseChoices
        # that belong to other sets.

        # 3) A user can have more than one UserVerseStatus for the same
        # verse. If these are not in 'passage' type sets, we want them all
        # to be updated.

        if verse_set_id is None:
            verse_set = None
        else:
            verse_set = VerseSet.objects.get(id=verse_set_id)

        if verse_set is not None and verse_set.set_type == VerseSetType.PASSAGE:
            # Look for verse choices in this VerseSet, but not any others.
            start_qs = self.verse_statuses.filter(verse_choice__verse_set=verse_set)
            verse_choices = verse_set.verse_choices.all()

        else:
            # Look for verse choices for same reference, but not for 'passage' set types
            start_qs = self.verse_statuses.filter(verse_choice__reference=reference)
            start_qs = start_qs.exclude(verse_choice__verse_set__set_type=VerseSetType.PASSAGE)
            verse_choices = VerseChoice.objects.filter(reference=reference)
            verse_choices = verse_choices.exclude(verse_set__set_type=VerseSetType.PASSAGE)


        # 'old' = ones with old, incorrect version
        old = start_qs.exclude(version__slug=version_slug)
        # 'correct' = ones with newly selected, correct version
        correct = start_qs.filter(version__slug=version_slug)

        # If they had no test data, it is safe to delete, and this keeps things
        # trim:
        old.filter(last_tested__isnull=True).delete()
        # Otherwise just set ignored
        old.update(ignored=True)

        # For each VerseChoice, we need to create a new UserVerseStatus if
        # one with new version doesn't exist, or update 'ignored' if it
        # does.
        correct_l = list(correct.select_related('verse_choice'))
        correct.update(ignored=False)

        # Now we need to see if we need to create any new UserVerseStatuses.
        verse_choices = list(verse_choices)

        missing = set(verse_choices) - set([vs.verse_choice for vs in correct_l])
        if missing:
            version = BibleVersion.objects.get(slug=version_slug)
            for verse_choice in missing:
                self.create_verse_status(verse_choice=verse_choice,
                                         version=version)

    def get_verse_status_for_ref(self, reference, verse_set_id):
        l = self.verse_statuses.filter(ignored=False, verse_choice__reference=reference)
        # This is used by 'get next verse' handler, when we need the following
        l = l.select_related('version', 'verse_choice', 'verse_choice__verse_set')
        if verse_set_id is None:
            l = l.filter(verse_choice__verse_set__isnull=True)
        else:
            l = l.filter(verse_choice__verse_set=verse_set_id)
        l = list(l)
        if len(l) == 0:
            return None

        # There is the possibility of multiple here, but they should all be the
        # same, so we return any.
        return l[0]


    def create_verse_status(self, verse_choice, version):
        uvs, new = self.verse_statuses.get_or_create(verse_choice=verse_choice,
                                                     version=version)

        same_verse = self.verse_statuses.filter(verse_choice__reference=verse_choice.reference,
                                                version=version).exclude(id=uvs.id)

        # NB: we are exploiting the fact that multiple calls to
        # create_verse_status will get slightly increasing values of 'added',
        # allowing us to preserve order.
        if new:
            uvs.added = timezone.now()

        if same_verse and new:
            # Use existing data:
            same_verse = same_verse[0]
            uvs.memory_stage = same_verse.memory_stage
            uvs.strength = same_verse.strength
            uvs.added = same_verse.added
            uvs.first_seen = same_verse.first_seen
            uvs.last_tested = same_verse.last_tested

        return uvs

    def _dedupe_uvs_set(self, uvs_set):
        # Need to dedupe (due to VerseChoice objects that belong to different
        # VerseSets). Also need to iterate over the result multiple times and
        # get length etc., so use list instead of generator.
        retval = []
        seen_refs = set()
        for uvs in uvs_set:
            if uvs.verse_choice.reference in seen_refs:
                continue
            seen_refs.add(uvs.verse_choice.reference)
            retval.append(uvs)
        return retval

    def verse_statuses_for_revising(self):
        """
        Returns a query set of UserVerseStatuses that need revising.
        """
        import time
        now_seconds = time.time()
        qs = (self.verse_statuses
              .filter(ignored=False,
                      memory_stage=MemoryStage.TESTED)
              .exclude(verse_choice__verse_set__set_type=VerseSetType.PASSAGE)
              .select_related('verse_choice'))
        qs = memorymodel.filter_qs(qs, now_seconds)
        return self._dedupe_uvs_set(qs)

    def verse_statuses_for_learning_qs(self):
        qs = self.verse_statuses.filter(ignored=False, memory_stage__lt=MemoryStage.TESTED)
        # Don't include passages - we do those separately
        qs = qs.exclude(verse_choice__verse_set__set_type=VerseSetType.PASSAGE)
        return qs

    def verse_statuses_for_learning(self):
        """
        Returns a list of UserVerseStatuses that need learning.
        """
        qs = self.verse_statuses_for_learning_qs()
        # Optimise for accessing 'reference'
        qs = qs.select_related('verse_choice')
        # 'added' should have enough precision to distinguish, otherwise 'id'
        # should be according to order of creation.
        qs = qs.order_by('added', 'id')
        return self._dedupe_uvs_set(qs)

    def clear_learning_queue(self):
        self.verse_statuses_for_learning_qs().delete()

    def passages_for_learning(self):
        """
        Retrieves a list of VerseSet objects of 'passage' type that need
        more initial learning.
        They are decorated with 'untested_total' and 'tested_total' attributes.
        """
        statuses = self.verse_statuses.filter(verse_choice__verse_set__set_type=VerseSetType.PASSAGE,
                                              ignored=False,
                                              memory_stage__lt=MemoryStage.TESTED)\
                                              .select_related('verse_choice',
                                                              'verse_choice__verse_set')
        verse_sets = {}

        # We already have info needed for untested_total
        for s in statuses:
            vs_id = s.verse_choice.verse_set.id
            if vs_id not in verse_sets:
                vs = s.verse_choice.verse_set
                verse_sets[vs_id] = vs
                vs.untested_total = 0
            else:
                vs = verse_sets[vs_id]

            vs.untested_total += 1

        # We need one additional query per VerseSet for untested_total
        for vs in verse_sets.values():
            vs.tested_total = self.verse_statuses.filter(verse_choice__verse_set=vs,
                                                         ignored=False,
                                                         memory_stage__gte=MemoryStage.TESTED).count()
        return verse_sets.values()

    def passages_for_revising(self):
        import time
        now_seconds = time.time()
        statuses = self.verse_statuses.filter(verse_choice__verse_set__set_type=VerseSetType.PASSAGE,
                                              ignored=False,
                                              memory_stage__gte=MemoryStage.TESTED)\
                                              .select_related('verse_choice',
                                                              'verse_choice__verse_set')

        # If any of them need revising, we want to know about it:
        statuses = memorymodel.filter_qs(statuses, now_seconds)

        # However, we want to exclude those which have any verses in the set
        # still untested. This is tricky to do in SQL/Django's ORM, so we hope
        # that 'statuses' gives a fairly small set of VerseSets and do
        # additional filtering in Python.

        verse_sets = set(uvs.verse_choice.verse_set for uvs in statuses)
        all_statuses = self.verse_statuses.filter(verse_choice__verse_set__in=verse_sets)\
            .select_related('verse_choice',
                            'verse_choice__verse_set')

        for uvs in all_statuses:
            if uvs.memory_stage < MemoryStage.TESTED:
                verse_sets.discard(uvs.verse_choice.verse_set)

        return sorted(list(verse_sets), key=lambda vs: vs.name)

    def verse_statuses_for_passage(self, verse_set_id):
        # Must be strictly in the bible order, so don't rely on ('added', id') for
        # ordering. We must get the verses and compare bible_verse_number.
        l = list(self.verse_statuses.filter(verse_choice__verse_set=verse_set_id,
                                            ignored=False).select_related('verse_choice'))
        refs = [uvs.reference for uvs in l]
        verse_list = self.default_bible_version.get_verses_by_reference_bulk(refs)
        for uvs in l:
            v = verse_list[uvs.reference]
            uvs.bible_verse_number = v.bible_verse_number
        l.sort(key=lambda uvs: uvs.bible_verse_number)
        return l

    def cancel_passage(self, verse_set_id):
        # For passages, the UserVerseStatuses may be already tested.
        # We don't want to lose that info, therefore set to 'ignored',
        # rather than delete() (unlike clear_learning_queue)
        self.verse_statuses\
            .filter(verse_choice__verse_set=verse_set_id, ignored=False)\
            .update(ignored=True)
