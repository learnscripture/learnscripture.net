from datetime import timedelta
import itertools

from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password
from django.utils.functional import cached_property
from django.utils import timezone

from accounts import memorymodel
from bibleverses.models import BibleVersion, MemoryStage, StageType, BibleVersion, VerseChoice, VerseSet, VerseSetType, get_passage_sections
from scores.models import TotalScore, ScoreReason, Scores, get_rank_all_time, get_rank_this_week

from learnscripture.datastructures import make_choices


SubscriptionType = make_choices('SubscriptionType',
                                [(0, 'FREE_TRIAL', 'Free trial'),
                                 (1, 'PAID_UP', 'Paid up'),
                                 (2, 'BASIC', 'Basic account (free)'),
                                 (3, 'LIFETIME_FREE', 'Lifetime free')]
                                )

TestingMethod = make_choices('TestingMethod',
                             [(0, 'FULL_WORDS', 'Full words - recommended for full keyboards and normal typing skills'),
                              (1, 'FIRST_LETTER', 'First letter - recommended for handheld devices and slower typers')]
                             )

THEMES = [('calm', 'Slate'),
          ('bubblegum', 'Bubblegum pink'),
          ('bubblegum2', 'Bubblegum green'),
          ('space', 'Space'),
          ]


# Account is separate from Identity to allow guest users to use the site fully
# without signing up.
#
# Everything related to learning verses is related to Identity.
# Social aspects and payment aspects are related to Account.
# Identity methods are the main interface for most business logic,
# and so sometimes they just delegate to Account methods.

class AccountManager(models.Manager):
    def create(self, *args, **kwargs):
        obj = super(AccountManager, self).create(*args, **kwargs)
        TotalScore.objects.create(account=obj)
        return obj


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

    objects = AccountManager()

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

    def award_action_points(self, reference, text,
                            old_memory_stage, action_change,
                            action_stage, accuracy):
        if not self.scoring_enabled():
            return []

        if action_stage != StageType.TEST:
            return []

        score_logs = []
        # This logic is reproduced client side in order to display target
        word_count = len(text.strip().split())
        max_points = word_count * Scores.POINTS_PER_WORD
        if old_memory_stage >= MemoryStage.TESTED:
            reason = ScoreReason.VERSE_REVISED
        else:
            reason = ScoreReason.VERSE_TESTED
        points = max_points * accuracy
        score_logs.append(self.add_points(points, reason))

        if accuracy == 1:
            score_logs.append(self.add_points(points * Scores.PERFECT_BONUS_FACTOR,
                                              ScoreReason.PERFECT_TEST_BONUS))

        if (action_change.old_strength < memorymodel.LEARNT <= action_change.new_strength):
            score_logs.append(self.add_points(word_count * Scores.POINTS_PER_WORD *
                                              Scores.VERSE_LEARNT_BONUS,
                                              ScoreReason.VERSE_LEARNT))
        return score_logs

    def award_revision_complete_bonus(self, score_log_ids):
        if not self.scoring_enabled():
            return []

        points = self.score_logs.filter(id__in=score_log_ids).aggregate(models.Sum('points'))['points__sum'] * Scores.REVISION_COMPLETE_BONUS_FACTOR
        return [self.add_points(points, ScoreReason.REVISION_COMPLETED)]

    def add_points(self, points, reason):
        return self.score_logs.create(points=points,
                                      reason=reason)

    def get_score_logs(self, from_datetime):
        return self.score_logs.filter(created__gte=from_datetime).order_by('created')

    def scoring_enabled(self):
        return self.subscription != SubscriptionType.BASIC

    @cached_property
    def points_all_time(self):
        return self.total_score.points

    @cached_property
    def rank_all_time(self):
        return get_rank_all_time(self.total_score)

    @cached_property
    def points_this_week(self):
        n = timezone.now()
        return self.score_logs.filter(created__gt=n - timedelta(7))\
            .aggregate(models.Sum('points'))['points__sum']

    @cached_property
    def rank_this_week(self):
        return get_rank_this_week(self.points_this_week)


class ActionChange(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


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
    enable_animations = models.BooleanField(blank=True, default=True)
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

    def prepare_for_learning(self):
        if self.account_id is not None:
            TotalScore.objects.get_or_create(account=self.account)

    def add_verse_set(self, verse_set, version=None):
        """
        Adds the verses in a VerseSet to the user's UserVerseStatus objects,
        and returns the UserVerseStatus objects.
        """
        if version is None:
            version = self.default_bible_version

        out = []

        vc_list = verse_set.verse_choices.all()
        existing_uvss = set(self.verse_statuses.filter(verse_set=verse_set, version=version,
                                                       ignored=False))

        uvss_dict = dict([(uvs.reference, uvs) for uvs in existing_uvss])

        if verse_set.set_type == VerseSetType.SELECTION:
            # Prefer existing UVSs of different versions if they are used.
            other_versions = self.verse_statuses.filter(
                verse_set__set_type=VerseSetType.SELECTION,
                ignored=False,
                reference__in=[vc.reference for vc in vc_list])\
                .select_related('version')
            other_version_dict = dict([(uvs.reference, uvs) for uvs in other_versions])
        else:
            other_version_dict = {}

        # Want to preserve order of verse_set, so iterate like this:
        for vc in vc_list:
            if vc.reference in uvss_dict:
                # Save work - create_verse_status is expensive
                out.append(uvss_dict[vc.reference])
            else:
                if vc.reference in other_version_dict:
                    use_version = other_version_dict[vc.reference].version
                else:
                    use_version = version
                # Otherwise we set the version to the chosen one
                new_uvs = self.create_verse_status(vc.reference, verse_set, use_version)
                new_uvs.ignored = False
                new_uvs.save()
                out.append(new_uvs)
        verse_set.mark_chosen()

        return out

    def add_verse_choice(self, reference, version=None):
        if version is None:
            version = self.default_bible_version

        existing = list(self.verse_statuses.filter(reference=reference, ignored=False))
        if existing:
            return existing[0]
        else:
            return self.create_verse_status(reference, None, version)

    def record_verse_action(self, reference, version_slug, stage_type, accuracy=None):
        """
        Records an action such as 'READ' or 'TESTED' against a verse.
        Returns an ActionChange object.
        """
        # We keep this separate from award_action_points because it needs
        # different info, and it is easier to test with its current API.

        s = self.verse_statuses.filter(reference=reference,
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
            return ActionChange(old_strength=old_strength, new_strength=new_strength)

        if mem_stage == MemoryStage.SEEN:
            s.filter(first_seen__isnull=True).update(first_seen=now)
            return ActionChange()

    def award_action_points(self, reference, text, old_memory_stage, action_change,
                            action_stage, accuracy):
        if self.account_id is None:
            return []

        return self.account.award_action_points(reference, text, old_memory_stage, action_change,
                                                action_stage, accuracy)

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
            start_qs = self.verse_statuses.filter(verse_set=verse_set)
            verse_choices = verse_set.verse_choices.all()
            needed_uvss = [(verse_set, vc.reference) for vc in verse_choices]

        else:
            # Look for verse choices for same reference, but not for 'passage' set types
            start_qs = self.verse_statuses.filter(reference=reference).select_related('verse_set')
            start_qs = start_qs.exclude(verse_set__set_type=VerseSetType.PASSAGE)
            # Need a UVS for each set the user already has a UVS for.
            needed_uvss = [(uvs.verse_set, reference) for uvs in start_qs]


        # 'old' = ones with old, incorrect version
        old = start_qs.exclude(version__slug=version_slug)
        # 'correct' = ones with newly selected, correct version
        correct_version = start_qs.filter(version__slug=version_slug)

        # If they had no test data, it is safe to delete, and this keeps things
        # trim:
        old.filter(last_tested__isnull=True).delete()
        # Otherwise just set ignored
        old.update(ignored=True)

        # For each VerseChoice, we need to create a new UserVerseStatus if
        # one with new version doesn't exist, or update 'ignored' if it
        # does.
        correct_version_l = list(correct_version.all())
        correct_version.update(ignored=False)

        # Now we need to see if we need to create any new UserVerseStatuses.
        missing = set(needed_uvss) - set([(uvs.verse_set,  uvs.reference)
                                          for uvs in correct_version_l])
        if missing:
            version = BibleVersion.objects.get(slug=version_slug)
            for (vs, ref) in missing:
                self.create_verse_status(reference=ref,
                                         verse_set=vs,
                                         version=version)

    def get_verse_statuses_bulk(self, references):
        # refs is a list of (verse_set_id, ref) tuples
        # Returns a dictionary of (verse_set_id, ref): UVS
        # The UVS objects have 'text' attributes retrieved efficiently.

        # For efficiency, we group by verse_set_id to minimize queries
        references = sorted(references)
        groups = []
        for verse_set_id, g in itertools.groupby(references,
                                                 lambda (verse_set_id, ref): verse_set_id):
            groups.append((verse_set_id, [ref for verse_set_id, ref in g]))


        retval = {}
        for verse_set_id, references in groups:
            l = self.verse_statuses.filter(ignored=False, reference__in=references)
            # This is used by VersesToLearnHandler, where we need the following:
            l = l.select_related('version', 'verse_set')
            if verse_set_id is None:
                l = l.filter(verse_set__isnull=True)
            else:
                l = l.filter(verse_set=verse_set_id)
            l = list(l)

            # HACK. The needs_testing_override fix applied in passages_for_revising
            # doesn't get saved to the session. So we have to reapply it at this
            # point.

            # The 'better' fix would be to fix UserVerseStatus.needs_testing, but
            # that involves UserVerseStatus doing queries on the VerseSet
            # collection it belongs to.

            # An alternative is to save complete UserVerseStatus objects to
            # session, but this gets tricky when it comes to changing versions.

            if len(l) > 0:
                vs = l[0].verse_set
                if vs is not None and vs.set_type == VerseSetType.PASSAGE:
                    self._add_needs_testing_override(l)

            retval.update(dict(((verse_set_id, uvs.reference), uvs) for uvs in l))

        # We need to get 'text' efficiently too. Group into versions:
        by_version = {}
        for uvs in retval.values():
            by_version.setdefault(uvs.version_id, []).append(uvs)

        # Get the texts in bulk
        texts = {}
        for version_id, uvs_list in by_version.items():
            version = uvs_list[0].version
            refs = [uvs.reference for uvs in uvs_list]
            for ref, text in version.get_text_by_reference_bulk(refs).items():
                texts[version_id, ref] = text

        # Assign texts back to uvs:
        for uvs in retval.values():
            uvs.text = texts[uvs.version_id, uvs.reference]

        return retval

    def create_verse_status(self, reference, verse_set, version):
        # bible_verse_number has to be specified here since it is non-nullable
        bible_verse_number = version.get_verse_list(reference)[0].bible_verse_number
        uvs, new = self.verse_statuses.get_or_create(verse_set=verse_set,
                                                     reference=reference,
                                                     bible_verse_number=bible_verse_number,
                                                     version=version)

        same_verse = self.verse_statuses.filter(reference=reference,
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

    def cancel_learning(self, reference):
        """
        Cancel learning an individual verse.

        Ignores VerseChoices that belong to passage sets.
        """
        # Not used for passages verse sets.
        qs = self.verse_statuses.filter(reference=reference)
        qs = qs.exclude(verse_set__set_type=VerseSetType.PASSAGE)
        qs.update(ignored=True)

    def _dedupe_uvs_set(self, uvs_set):
        # Need to dedupe (due to nullable verse_set which allows
        # multiple (reference=ref, verse_set=NULL) pairs
        retval = []
        seen_refs = set()
        for uvs in uvs_set:
            if uvs.reference in seen_refs:
                continue
            seen_refs.add(uvs.reference)
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
              .exclude(verse_set__set_type=VerseSetType.PASSAGE)
              .order_by('added', 'id')
              )
        qs = memorymodel.filter_qs(qs, now_seconds)
        return self._dedupe_uvs_set(qs)

    def verse_statuses_for_learning_qs(self):
        qs = self.verse_statuses.filter(ignored=False, memory_stage__lt=MemoryStage.TESTED)
        # Don't include passages - we do those separately
        qs = qs.exclude(verse_set__set_type=VerseSetType.PASSAGE)
        return qs

    def verse_statuses_for_learning(self):
        """
        Returns a list of UserVerseStatuses that need learning.
        """
        qs = self.verse_statuses_for_learning_qs()
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
        statuses = self.verse_statuses.filter(verse_set__set_type=VerseSetType.PASSAGE,
                                              ignored=False,
                                              memory_stage__lt=MemoryStage.TESTED)\
                                              .select_related('verse_set')
        verse_sets = {}

        # We already have info needed for untested_total
        for s in statuses:
            vs_id = s.verse_set.id
            if vs_id not in verse_sets:
                vs = s.verse_set
                verse_sets[vs_id] = vs
                vs.untested_total = 0
            else:
                vs = verse_sets[vs_id]

            vs.untested_total += 1

        # We need one additional query per VerseSet for untested_total
        for vs in verse_sets.values():
            vs.tested_total = self.verse_statuses.filter(verse_set=vs,
                                                         ignored=False,
                                                         memory_stage__gte=MemoryStage.TESTED).count()
        return verse_sets.values()

    def passages_for_revising(self):
        import time
        now_seconds = time.time()
        statuses = self.verse_statuses.filter(verse_set__set_type=VerseSetType.PASSAGE,
                                              ignored=False,
                                              memory_stage__gte=MemoryStage.TESTED)\
                                              .select_related('verse_set')

        # If any of them need revising, we want to know about it:
        statuses = memorymodel.filter_qs(statuses, now_seconds)

        # However, we want to exclude those which have any verses in the set
        # still untested. This is tricky to do in SQL/Django's ORM, so we hope
        # that 'statuses' gives a fairly small set of VerseSets and do
        # additional filtering in Python.

        # We also need to know if group testing is on the cards, since that
        # allows for the possibility of splitting into sections for section
        # learning.

        verse_sets = set(uvs.verse_set for uvs in statuses)
        group_testing = dict((vs.id, True) for vs in verse_sets)
        all_statuses = self.verse_statuses.filter(verse_set__in=verse_sets)\
            .select_related('verse_set')

        for uvs in all_statuses:
            if uvs.memory_stage < MemoryStage.TESTED:
                verse_sets.discard(uvs.verse_set)
            if uvs.strength <= memorymodel.STRENGTH_FOR_GROUP_TESTING:
                group_testing[uvs.verse_set_id] = False

        # Decorate with info about possibility of combining
        vss = list(verse_sets)
        for vs in vss:
            vs.splittable = vs.breaks != "" and group_testing[vs.id]

        return sorted(vss, key=lambda vs: vs.name)

    def _add_needs_testing_override(self, uvs_list):
        # For passages, we adjust 'needs_testing' to get the passage to be
        # tested together. See explanation in memorymodel
        min_strength = min(uvs.strength for uvs in uvs_list)
        if min_strength > memorymodel.STRENGTH_FOR_GROUP_TESTING:
            for uvs in uvs_list:
                uvs.needs_testing_override = True

    def verse_statuses_for_passage(self, verse_set_id):
        # Must be strictly in the bible order
        l = list(self.verse_statuses.filter(verse_set=verse_set_id,
                                            ignored=False).order_by('bible_verse_number'))
        self._add_needs_testing_override(l)

        return l

    def get_next_section(self, uvs_list, verse_set):
        """
        Given a UVS list and a VerseSet, get the items in uvs_list
        which are the next section to revise.
        """
        # We don't track which was the last 'section' learnt, and we can't,
        # since the user can give up at any point.  We therefore use heuristics
        # to work out which should be the next section.

        if verse_set.breaks == '' or len(uvs_list) == 0:
            return uvs_list

        # First split into sections according to the specified breaks
        sections = get_passage_sections(uvs_list, verse_set.breaks)

        # For each section, work out if it has been tested 'together'
        section_info = {} # section idx: info dict
        for i, section in enumerate(sections):
            max_last_tested = max(uvs.last_tested for uvs in section)
            min_last_tested = min(uvs.last_tested for uvs in section)
            # It should take no more than 2 minutes to test a single verse,
            # being conservative
            tested_together = ((max_last_tested - min_last_tested).total_seconds() <
                                  2 * 60 * len(section))
            section_info[i] = {'tested_together': tested_together,
                               'last_tested': min_last_tested}


        # Find which section was tested together last.
        last_section_tested = None
        overall_max_last_tested = None
        for i, info in section_info.items():
            if info['tested_together']:
                if (overall_max_last_tested is None or
                    info['last_tested'] > overall_max_last_tested):
                    overall_max_last_tested = info['last_tested']
                    last_section_tested = i

        if last_section_tested is None:
            # Implies no section has been tested before as a group. So test the
            # first section.
            return sections[0]

        # Go for the section after the last section that was tested together
        # (wrapping round if necessary)
        section_num = (last_section_tested + 1) % len(sections)

        # Ideally, we would return a verse of context with
        # 'needs_testing_override' being set to False.  However, that doesn't
        # currently survive being saved to the session. See 'HACK' and
        # _add_needs_testing_override().

        return sections[section_num]

    def slim_passage_for_revising(self, uvs_list, verse_set):
        """
        Uses breaks defined for the verse set to slim a passage
        down if not all verses need testing.
        """

        if verse_set.breaks == '' or len(uvs_list) == 0:
            return uvs_list

        # First split into sections according to the specified breaks
        sections = get_passage_sections(uvs_list, verse_set.breaks)

        to_test = []
        for section in sections:
            if (any(uvs.needs_testing for uvs in section)):
                to_test.extend(section)

        return to_test


    def cancel_passage(self, verse_set_id):
        # For passages, the UserVerseStatuses may be already tested.
        # We don't want to lose that info, therefore set to 'ignored',
        # rather than delete() (unlike clear_learning_queue)
        self.verse_statuses\
            .filter(verse_set=verse_set_id, ignored=False)\
            .update(ignored=True)

    def verse_sets_visible(self):
        """
        Gets a QuerySet of all VerseSets that are visible for this identity
        """
        qs = VerseSet.objects.public()
        if self.account_id is not None:
            qs = qs | self.account.verse_sets_created.all()
        return qs

    def get_score_logs(self, from_datetime):
        if self.account_id is None:
            return []
        else:
            return self.account.get_score_logs(from_datetime)

    def scoring_enabled(self):
        if self.account_id is None:
            return False
        return self.account.scoring_enabled()

    def award_revision_complete_bonus(self, score_log_ids):
        if self.account_id is None:
            return []
        else:
            return self.account.award_revision_complete_bonus(score_log_ids)
