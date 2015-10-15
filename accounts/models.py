from __future__ import unicode_literals

from collections import defaultdict, OrderedDict
from datetime import timedelta
import itertools
import math

from django.conf import settings
from django.core import mail
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.contrib.sites.models import get_current_site
from django.template import loader
from django.utils.functional import cached_property

from accounts import memorymodel
from accounts.signals import verse_started, verse_tested, verse_finished, points_increase, scored_100_percent, catechism_started
from bibleverses.models import TextVersion, MemoryStage, StageType, VerseSet, VerseSetType, UserVerseStatus, TextType, get_passage_sections, InvalidVerseReference, count_words
from bibleverses.signals import verse_set_chosen
from scores.models import TotalScore, ScoreReason, Scores, get_rank_all_time, get_rank_this_week
from tracking.models import track_querysets

from learnscripture.datastructures import make_choices
from learnscripture.utils.cache import cache_results, clear_cache_results


TestingMethod = make_choices('TestingMethod',
                             [(0, 'FULL_WORDS', 'Full words - recommended for full keyboards and normal typing skills'),
                              (1, 'FIRST_LETTER', 'First letter - recommended for slower typers'),
                              (2, 'ON_SCREEN', 'On screen buttons - recommended for handheld devices'),
                              ])

THEMES = [('calm', 'Slate'),
          ('bubblegum', 'Bubblegum pink'),
          ('bubblegum2', 'Bubblegum green'),
          ('space', 'Space'),
          ]
THEME_FONTS = [
    ('calm', ['http://fonts.googleapis.com/css?family=Belleza']),
    ('bubblegum', ['http://fonts.googleapis.com/css?family=Short+Stack']),
    ('bubblegum2', ['http://fonts.googleapis.com/css?family=Short+Stack']),
    ('space', ['http://fonts.googleapis.com/css?family=Prosto+One']),
]
DEFAULT_THEME = 'calm'

DONT_NAG_NEW_USERS_FOR_MONEY_DAYS = 30

# Account is separate from Identity to allow guest users to use the site fully
# without signing up.
#
# Everything related to learning verses is related to Identity.
# Social aspects and payment aspects are related to Account.
# Identity methods are the main interface for most business logic,
# and so sometimes they just delegate to Account methods.


class AccountManager(UserManager):
    def visible_for_account(self, account):
        qs = self.active()
        if account is None or not account.is_hellbanned:
            # Only hellbanned users see each other
            qs = qs.exclude(is_hellbanned=True)
        return qs

    def active(self):
        return self.get_query_set().filter(is_active=True)

    def send_reminders_to(self):
        return self.active().filter(remind_after__gt=0,
                                    email_bounced__isnull=True)


class Account(AbstractBaseUser):
    username = models.CharField(max_length=100, blank=False, unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    date_joined = models.DateTimeField(default=timezone.now)
    is_tester = models.BooleanField(default=False, blank=True)
    is_moderator = models.BooleanField(default=False, blank=True)
    is_under_13 = models.BooleanField("Under 13 years old",
                                      default=False, blank=True)
    is_active = models.BooleanField(default=True)
    enable_commenting = models.BooleanField("Enable comment system",
                                            default=True, blank=True)

    # A hellbanned user is barred from interaction with other users, and any
    # visibility by other users, but they not aware of that. They see an
    # alternate reality, which includes normal user and other hellbanned users.
    # This may not work perfectly with respect to things that are calculated
    # globally.
    is_hellbanned = models.BooleanField(default=False)

    has_installed_android_app = models.BooleanField(default=False)

    # Email reminder preferences and meta data
    remind_after = models.PositiveSmallIntegerField(
        "Send email reminders after (days)", default=2)
    remind_every = models.PositiveSmallIntegerField(
        "Send email reminders every (days)", default=3)
    last_reminder_sent = models.DateTimeField(null=True, blank=True)

    email_bounced = models.DateTimeField(null=True, blank=True)

    # Attributes needed for admin login and auth.contrib compat
    is_superuser = models.BooleanField(default=False)

    # Following:
    following = models.ManyToManyField('self',
                                       symmetrical=False,
                                       blank=True,
                                       related_name='followers')

    # Managers and meta
    objects = AccountManager()

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ['username']

    def save(self, **kwargs):
        # We need to ensure that there is a TotalScore object
        if self.id is None:
            retval = super(Account, self).save(**kwargs)
            TotalScore.objects.create(account=self)
            return retval
        else:
            return super(Account, self).save(**kwargs)

    # admin login stuff
    @property
    def is_staff(self):
        return self.is_superuser

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    def get_short_name(self):
        return self.first_name

    # Friendly wrappers
    @property
    def email_name(self):
        return self.first_name if self.first_name.strip() != "" else self.username

    @property
    def personal_name(self):
        return (self.first_name.strip() + u' ' + self.last_name.strip()).strip()

    @property
    def recruited_by(self):
        return self.identity.referred_by

    def __unicode__(self):
        return self.username

    # Main business logic
    def award_action_points(self, reference, text,
                            old_memory_stage, action_change,
                            action_stage, accuracy):
        if action_stage != StageType.TEST:
            return []

        score_logs = []
        word_count = count_words(text)
        max_points = word_count * Scores.POINTS_PER_WORD
        if old_memory_stage >= MemoryStage.TESTED:
            reason = ScoreReason.VERSE_REVISED
        else:
            reason = ScoreReason.VERSE_TESTED
        points = max_points * accuracy
        score_logs.append(self.add_points(points, reason, accuracy=accuracy, reference=reference))

        if accuracy == 1:
            score_logs.append(self.add_points(points * Scores.PERFECT_BONUS_FACTOR,
                                              ScoreReason.PERFECT_TEST_BONUS,
                                              reference=reference,
                                              accuracy=accuracy))
            # At least one subscriber to scored_100_percent relies on score_logs
            # to be created in order to do job. In context of tests, this means
            # we have to send this signal after creating ScoreLog
            scored_100_percent.send(sender=self)

        if (action_change.old_strength < memorymodel.LEARNT <= action_change.new_strength):
            score_logs.append(self.add_points(word_count * Scores.POINTS_PER_WORD *
                                              Scores.VERSE_LEARNT_BONUS,
                                              ScoreReason.VERSE_LEARNT,
                                              reference=reference,
                                              accuracy=accuracy))
            verse_finished.send(sender=self)

        if action_stage == StageType.TEST and old_memory_stage < MemoryStage.TESTED:
            verse_started.send(sender=self)

        return score_logs

    def add_points(self, points, reason, accuracy=None, reference=""):
        # Need to refresh 'total_score' each time
        points = math.floor(points)
        current_points = TotalScore.objects.get(account_id=self.id).points
        score_log = self.score_logs.create(points=points,
                                           reason=reason,
                                           reference=reference,
                                           accuracy=accuracy)
        # Change cached object to reflect DB, which has been
        # updated via a SQL UPDATE for max correctness.
        self.total_score.points = current_points + points
        points_increase.send(sender=self,
                             previous_points=current_points,
                             points_added=score_log.points)
        return score_log

    def get_score_logs(self, from_datetime):
        return self.score_logs.filter(created__gte=from_datetime).order_by('created')

    @cached_property
    def points_all_time(self):
        return self.total_score.points

    @cached_property
    def rank_all_time(self):
        return get_rank_all_time(self.total_score, self.is_hellbanned)

    @cached_property
    def points_this_week(self):
        n = timezone.now()
        val = self.score_logs.filter(created__gt=n - timedelta(7))\
            .aggregate(models.Sum('points'))['points__sum']
        return val if val is not None else 0

    @cached_property
    def rank_this_week(self):
        return get_rank_this_week(self.points_this_week, self.is_hellbanned)

    def receive_payment(self, ipn_obj):
        if ipn_obj.mc_currency == settings.VALID_RECEIVE_CURRENCY:
            amount = ipn_obj.mc_gross
        elif ipn_obj.settle_currency == settings.VALID_RECEIVE_CURRENCY:
            amount = ipn_obj.settle_amount
        else:
            raise ValueError("Unrecognised currency")
        self.payments.create(amount=amount,
                             paypal_ipn=ipn_obj,
                             created=timezone.now())
        send_payment_received_email(self, ipn_obj)

    def make_referral_link(self, url):
        if '?from=' in url or '&from=' in url:
            return url
        if '?' in url:
            url = url + '&'
        else:
            url = url + '?'
        url = url + 'from=' + self.username
        return url

    def referred_identities_count(self):
        return self.referrals.count()

    def visible_awards(self):
        all_awards = self.awards.order_by('award_type', 'level')
        visible = OrderedDict()
        # Ignore all but the highest
        for a in all_awards:
            if a.award_class.removed:
                continue
            visible[a.award_type] = a
        return sorted(visible.values(), key=lambda a: a.created, reverse=True)

    def add_html_notice(self, notice):
        return self.identity.add_html_notice(notice)

    def _memberships_with_group(self):
        return self.memberships.select_related('group').order_by('group__name')

    def get_groups(self):
        return [m.group for m in self._memberships_with_group()]

    def get_public_groups(self):
        return [m.group for m in self._memberships_with_group().filter(group__public=True)]

    def get_ordered_groups(self):
        from groups.models import Group
        # use Group directly so that we can do the annotation/ordering we need
        return (Group.objects
                .annotate(num_members=models.Count('members'))
                .order_by('-num_members')
                .filter(members=self)
                )

    def get_friendship_weights(self):
        """
        Returns a dictionary of {account_id: friendship_level} for this account.
        Friendship weight goes from value 0 to 1.
        """
        return account_get_friendship_weights(self.id)

    def android_app_installed(self):
        if not self.has_installed_android_app:
            self.has_installed_android_app = True
            self.save()
            self.add_html_notice('Thanks for installing the Android app! Please remember to <a href="https://play.google.com/store/apps/details?id=net.learnscripture.webviewapp">rate it and leave any comments you have!</a>')

    def donations_disabled(self):
        return (self.is_under_13 or
                ((timezone.now() - self.date_joined).days < DONT_NAG_NEW_USERS_FOR_MONEY_DAYS))

    def is_following(self, account):
        return self.following.filter(pk=account.id).exists()

    def follow_user(self, account):
        self.following.add(account)
        clear_friendship_weight_cache(self.id)

    def unfollow_user(self, account):
        self.following.remove(account)
        clear_friendship_weight_cache(self.id)

    @property
    def verse_sets_editable(self):
        if self.is_superuser:
            return VerseSet.objects.all()
        else:
            return self.verse_sets_created

    def can_edit_verse_set(self, verse_set):
        return self.is_superuser or self == verse_set.created_by


def normlise_weighting(weights):
    if not weights:
        return
    max_weight = max(weights.values())
    for k, v in weights.items():
        weights[k] = v / max_weight


@cache_results(seconds=1200)
def account_get_friendship_weights(account_id):
    # We use groups to define possible friendships.
    account = Account.objects.get(id=account_id)
    from groups.models import Membership
    weights = defaultdict(int)
    for m in Membership.objects.filter(account=account_id).select_related('group').prefetch_related('group__members'):
        group = m.group
        members = list(group.members.all())
        # Smaller groups are better evidence of friendship.
        w = 1.0 / len(members)
        for m in members:
            weights[m.id] += w

    # It's nice to see yourself in the event stream, but not that
    # important, so we first remove self.id, so it doesn't affect
    # normalisation, then add it back at level 0.5

    try:
        del weights[account_id]
    except KeyError:
        pass

    # Normalise to 1
    normlise_weighting(weights)

    # We use following as definite friendships. Following is the worth more than
    # any evidence from groups.
    for acc in account.following.all():
        weights[acc.id] += 1.5

    # Normalise again
    normlise_weighting(weights)

    # Give some weight to self
    weights[account_id] = 0.3

    return weights


def clear_friendship_weight_cache(account_id):
    clear_cache_results(account_get_friendship_weights, account_id)


def send_payment_received_email(account, payment):
    from django.conf import settings
    c = {
        'site': get_current_site(None),
        'payment': payment,
        'account': account,
    }

    body = loader.render_to_string("learnscripture/payment_received_email.txt", c)
    subject = u"LearnScripture.net - donation received"
    mail.send_mail(subject, body, settings.SERVER_EMAIL, [account.email])


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
    default_bible_version = models.ForeignKey(TextVersion, null=True, blank=True)
    desktop_testing_method = models.PositiveSmallIntegerField(choices=TestingMethod.choice_list,
                                                              default=TestingMethod.FULL_WORDS)
    touchscreen_testing_method = models.PositiveSmallIntegerField(choices=TestingMethod.choice_list,
                                                                  default=TestingMethod.ON_SCREEN)
    enable_animations = models.BooleanField(blank=True, default=True)
    enable_sounds = models.BooleanField(blank=True, default=False)
    enable_vibration = models.BooleanField("Vibrate on mistakes", blank=True, default=True)
    interface_theme = models.CharField(max_length=30, choices=THEMES,
                                       default=DEFAULT_THEME)
    referred_by = models.ForeignKey(Account, null=True, default=None,
                                    blank=True,
                                    related_name='referrals')

    track_learning = models.BooleanField(default=False)

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
        return self.default_bible_version is not None

    @property
    def default_to_dashboard(self):
        return self.preferences_setup

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

        if verse_set.is_selection:
            # Prefer existing UVSs of different versions if they are used.
            other_versions = self.verse_statuses.filter(
                verse_set__set_type=VerseSetType.SELECTION,
                ignored=False,
                reference__in=[vc.reference for vc in vc_list])\
                .select_related('version')
            other_version_dict = dict([(uvs.reference, uvs) for uvs in other_versions])
        elif verse_set.is_passage:
            # If they are already learning this passage in a different version,
            # use that version.
            verse_statuses = (self.verse_statuses
                              .filter(verse_set=verse_set,
                                      ignored=False)
                              .exclude(version=version)
                              )
            if len(verse_statuses) > 0:
                return self.add_verse_set(verse_set,
                                          version=verse_statuses[0].version)

            # Otherwise, we don't want a mixture of versions for learning a
            # passage set.
            other_version_dict = {}
        else:
            assert False, "Not reached"

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
                if new_uvs is not None:
                    out.append(new_uvs)

        verse_set_chosen.send(sender=verse_set, chosen_by=self.account)
        return out

    def add_verse_choice(self, reference, version=None):
        if version is None:
            version = self.default_bible_version

        existing = list(self.verse_statuses.filter(reference=reference,
                                                   verse_set__isnull=True,
                                                   ignored=False))
        if existing:
            return existing[0]
        else:
            return self.create_verse_status(reference, None, version)

    def add_catechism(self, catechism):
        """
        Add the QAPairs in a catechism to a user's UserVerseStatuses.
        """
        base_uvs_query = self.verse_statuses.filter(version=catechism)
        existing_uvss = base_uvs_query
        existing_refs = set(uvs.reference for uvs in existing_uvss)
        # Some might be set to 'ignored'. Need to fix that.
        if any(uvs.ignored for uvs in existing_uvss):
            base_uvs_query.update(ignored=False)

        qapairs = catechism.qapairs.all().order_by('order')

        new_uvss = [
            UserVerseStatus(
                for_identity=self,
                reference=qapair.reference,
                text_order=qapair.order,
                version=catechism,
                added=timezone.now()
            )
            for qapair in qapairs if qapair.reference not in existing_refs]
        UserVerseStatus.objects.bulk_create(new_uvss)
        return base_uvs_query.all().order_by('text_order')  # fresh QuerySet

    @track_querysets(lambda self, reference, *args, **kwargs: [self.verse_statuses.filter(reference=reference)],
                     lambda self, *args, **kwargs: self.track_learning)
    def record_verse_action(self, reference, version_slug, stage_type, accuracy=None):
        """
        Records an action such as 'READ' or 'TESTED' against a verse.
        Returns an ActionChange object.
        """
        # We keep this separate from award_action_points because it needs
        # different info, and it is easier to test with its current API.

        s = self.verse_statuses.filter(reference=reference,
                                       version__slug=version_slug).select_related('version')

        if len(s) == 0:
            # Shouldn't be possible via UI. The client must be trying to record
            # actions against verses they have never selected.
            return None

        mem_stage = {
            StageType.READ: MemoryStage.SEEN,
            StageType.TEST: MemoryStage.TESTED,
        }[stage_type]

        # It's possible that they have already been tested, so don't move them
        # down to MemoryStage.SEEN
        s.filter(memory_stage__lt=mem_stage).update(memory_stage=mem_stage)

        now = timezone.now()
        if mem_stage == MemoryStage.TESTED:
            s0 = s[0]  # Any should do, they should be all the same
            old_strength = s0.strength
            if s0.last_tested is None:
                time_elapsed = None
            else:
                time_elapsed = (now - s0.last_tested).total_seconds()
            new_strength = memorymodel.strength_estimate(old_strength, accuracy, time_elapsed)
            next_due = memorymodel.next_test_due(now, new_strength)
            s.update(strength=new_strength,
                     last_tested=now,
                     next_test_due=next_due)

            # Sometimes we get to here with 'first_seen' still null,
            # so we fix it to keep our data making sense.
            s.filter(strength__gt=0, first_seen__isnull=True).update(first_seen=now)

            verse_tested.send(sender=self, verse=s0)
            if (s0.version.is_catechism and s0.text_order == 1
                and old_strength == 0.0
                    and self.account_id is not None):
                catechism_started.send(self.account, catechism=s0.version)

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

        Returns a mapping: {old UVS id: new UVS id}
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

        if verse_set is not None and verse_set.is_passage:
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

        old_uvs_ids = [(uvs.reference, uvs.id) for uvs in old]

        # For each VerseChoice, we need to create a new UserVerseStatus if
        # one with new version doesn't exist, or update 'ignored' if it
        # does.
        correct_version_l = list(correct_version.all())
        correct_version.update(ignored=False)

        # Now we need to see if we need to create any new UserVerseStatuses.
        missing = set(needed_uvss) - set([(uvs.verse_set, uvs.reference)
                                          for uvs in correct_version_l])
        if missing:
            version = TextVersion.objects.get(slug=version_slug)
            for (vs, ref) in missing:
                self.create_verse_status(reference=ref,
                                         verse_set=vs,
                                         version=version)

        # Return value:
        final_correct_uvss = {uvs.reference: uvs for uvs in correct_version.all()}
        retval = {}
        for reference, uvs_id in old_uvs_ids:
            if reference in final_correct_uvss:
                retval[uvs_id] = final_correct_uvss[reference].id
            else:
                # No corresponding UVS, due to Verse.missing=True
                retval[uvs_id] = None

        if all(uvs_id is None for uvs_id in retval.values()):
            # There are no UVS objects for the destination version.  This
            # implies Verse.missing==True for the verses in the destination
            # version. In this case, we effectively cancel the 'change_version'
            # request.
            return {uvs_id: uvs_id for reference, uvs_id in old_uvs_ids}
        else:
            # creation of new UVS objects has succeeded, so 'remove' the old ones:
            # If they had no test data, it is safe to delete, and this keeps things
            # trim:
            old.filter(last_tested__isnull=True).delete()
            # Otherwise just set ignored
            old.update(ignored=True)

        return retval

    def get_verse_statuses_bulk(self, ids):
        # ids is a list of UserVerseStatus.id values
        # Returns a dictionary of {uvs.id: uvs}
        # The UVS objects have 'version', 'verse_set',
        # 'text', 'question', and 'answer' attributes retrieved efficiently,
        # as appropriate

        retval = {uvs.id: uvs for uvs in (self.verse_statuses
                                          .filter(id__in=ids)
                                          .select_related('version', 'verse_set'))
                  }

        # We need to get 'text' efficiently too. Group into versions:
        by_version = {}
        for uvs in retval.values():
            by_version.setdefault(uvs.version_id, []).append(uvs)

        # Get the texts/QAPairs in bulk
        texts = {}
        qapairs = {}
        suggestion_d = {}
        for version_id, uvs_list in by_version.items():
            version = uvs_list[0].version
            refs = [uvs.reference for uvs in uvs_list]
            for ref, text in version.get_text_by_reference_bulk(refs).items():
                # Bibles only here
                texts[version_id, ref] = text
            for ref, qapair in version.get_qapairs_by_reference_bulk(refs).items():
                # catechisms only here
                qapairs[version_id, ref] = qapair
            for ref, suggestions in version.get_suggestions_by_reference_bulk(refs).items():
                # Bibles and catechsims here
                suggestion_d[version_id, ref] = suggestions

        # Assign texts back to uvs:
        for uvs in retval.values():
            text = texts.get((uvs.version_id, uvs.reference), None)
            if text is not None:
                # Bible
                uvs.scoring_text = text
                uvs.title_text = uvs.reference

            qapair = qapairs.get((uvs.version_id, uvs.reference), None)
            if qapair is not None:
                # Catechism
                question, answer = qapair.question, qapair.answer
                uvs.scoring_text = answer
                uvs.title_text = uvs.reference + ". " + question
            uvs.suggestions = suggestion_d.get((uvs.version_id, uvs.reference), [])

        return retval

    def create_verse_status(self, reference, verse_set, version):
        try:
            verse_list = version.get_verse_list(reference)
        except InvalidVerseReference:
            # This can happen if Verse.missing==True for this version.
            return

        # text_order has to be specified in create since it is non-nullable
        text_order = verse_list[0].bible_verse_number
        # NB: we are exploiting the fact that multiple calls to
        # create_verse_status will get slightly increasing values of 'added',
        # allowing us to preserve order.
        uvs, new = self.verse_statuses.get_or_create(verse_set=verse_set,
                                                     reference=reference,
                                                     version=version,
                                                     defaults=dict(text_order=text_order,
                                                                   added=timezone.now()
                                                                   )
                                                     )

        dirty = False
        same_verse_set = self.verse_statuses.filter(reference=reference,
                                                    version=version).exclude(id=uvs.id)

        if same_verse_set and new:
            # Use existing data:
            same_verse = same_verse_set[0]
            uvs.memory_stage = same_verse.memory_stage
            uvs.strength = same_verse.strength
            # If previous record was ignored, it may have been cancelled, so we
            # ignore 'added' since otherwise it will interfere with ordering if
            # this is added to learning queue.
            if not same_verse.ignored:
                uvs.added = same_verse.added
            uvs.first_seen = same_verse.first_seen
            uvs.last_tested = same_verse.last_tested
            dirty = True

        if uvs.ignored:
            uvs.ignored = False
            dirty = True

        if dirty:
            uvs.save()

        return uvs

    def cancel_learning(self, references):
        """
        Cancel learning some verses.

        Ignores VerseChoices that belong to passage sets.
        """
        # Not used for passages verse sets.
        qs = self.verse_statuses.filter(reference__in=references)
        qs = qs.exclude(verse_set__set_type=VerseSetType.PASSAGE)
        qs.update(ignored=True)

    def reset_progress(self, reference, verse_set_id, version_slug):
        qs = self.verse_statuses.filter(reference=reference,
                                        version__slug=version_slug)
        if verse_set_id is None:
            qs = qs.filter(verse_set__isnull=True)
        else:
            qs = qs.filter(verse_set=verse_set_id)

        qs.update(strength=0,
                  last_tested=None,
                  next_test_due=None,
                  memory_stage=MemoryStage.ZERO)

    def _dedupe_uvs_set(self, uvs_set):
        # dedupe instances with same ref
        retval = []
        seen_refs = set()
        for uvs in uvs_set:
            if uvs.reference in seen_refs:
                continue
            seen_refs.add(uvs.reference)
            retval.append(uvs)
        return retval

    def _dedupe_uvs_set_distinguishing_verse_set(self, uvs_set):
        # Only dedupe multiple instances with same ref and verse_set==None
        retval = []
        seen_refs = set()
        for uvs in uvs_set:
            if uvs.verse_set_id is None:
                if uvs.reference in seen_refs:
                    continue
                seen_refs.add(uvs.reference)
            retval.append(uvs)
        return retval

    def verse_statuses_started(self):
        return self.verse_statuses.filter(ignored=False,
                                          strength__gt=0,
                                          last_tested__isnull=False)

    def verses_started_count(self, started_since=None):
        from scores.models import get_verses_started_counts
        return get_verses_started_counts([self.id],
                                         started_since=started_since
                                         )[self.id]

    def verses_finished_count(self, finished_since=None):
        from scores.models import get_verses_finished_count
        return get_verses_finished_count(self.id, finished_since=finished_since)

    def bible_verse_statuses_for_revising(self):
        """
        Returns a query set of UserVerseStatuses that need revising.
        """
        qs = (self.verse_statuses
              .filter(version__text_type=TextType.BIBLE,
                      ignored=False,
                      memory_stage=MemoryStage.TESTED)
              # Don't include passages - we do those separately:
              .exclude(verse_set__set_type=VerseSetType.PASSAGE)
              .order_by('next_test_due', 'added')
              )
        qs = memorymodel.filter_qs(qs, timezone.now())
        return self._dedupe_uvs_set(qs)

    def bible_verse_statuses_for_learning_qs(self):
        qs = (self.verse_statuses
              .filter(version__text_type=TextType.BIBLE,
                      ignored=False,
                      memory_stage__lt=MemoryStage.TESTED)
              # Don't include passages - we do those separately:
              .exclude(verse_set__set_type=VerseSetType.PASSAGE)
              )
        return qs

    def bible_verse_statuses_for_learning(self, verse_set_id):
        """
        Returns a list of UserVerseStatuses that need learning.

        If get_all=True, then all will be returned, otherwise the verse set
        specified in verse_set_id will be returned (with 'None' meaning no verse set)
        """
        qs = self.bible_verse_statuses_for_learning_qs()
        if verse_set_id is None:
            qs = qs.filter(verse_set__isnull=True)
        else:
            qs = qs.filter(verse_set=verse_set_id)

        # 'added' should have enough precision to distinguish, otherwise 'id'
        # should be according to order of creation.
        qs = qs.order_by('added', 'id')
        return self._dedupe_uvs_set(qs)

    def bible_verse_statuses_for_learning_grouped(self):
        qs = self.bible_verse_statuses_for_learning_qs()
        # Group by verse set, and eagerly load verse set, because we want to
        # group this way in the UI.  Use prefetch_related instead of
        # select_related because we are likely to have many UserVerseStatus
        # objects and very few VerseSet objects.
        qs = qs.order_by('verse_set', 'added', 'id').prefetch_related('verse_set')

        # We don't fully dedupe, because we want to distinguish
        # between UVSes with verse_set == None and verse_set != None
        uvs_list = self._dedupe_uvs_set_distinguishing_verse_set(qs)
        return [(a, list(b)) for a, b in
                itertools.groupby(uvs_list, lambda uvs: uvs.verse_set)]

    def clear_bible_learning_queue(self, verse_set_id):
        qs = self.bible_verse_statuses_for_learning_qs()
        if verse_set_id is None:
            qs = qs.filter(verse_set__isnull=True)
        else:
            qs = qs.filter(verse_set=verse_set_id)
        qs.delete()

    def _catechism_qas_base_qs(self, catechism_id):
        qs = (self.verse_statuses
              .filter(version__text_type=TextType.CATECHISM,
                      ignored=False)
              )
        if catechism_id is not None:
            qs = qs.filter(version=catechism_id)
        return qs

    def catechism_qas_for_learning_qs(self, catechism_id):
        return (self._catechism_qas_base_qs(catechism_id)
                .filter(memory_stage__lt=MemoryStage.TESTED)
                .order_by('added', 'id')
                )

    def catechism_qas_for_learning(self, catechism_id):
        """
        Returns catechism QAs that are queued for learning
        """
        return self.catechism_qas_for_learning_qs(catechism_id)

    def catechism_qas_for_revising(self, catechism_id):
        """
        Returns catechism QAs that are due for revising
        """
        qs = (self._catechism_qas_base_qs(catechism_id)
              .filter(memory_stage=MemoryStage.TESTED))
        qs = memorymodel.filter_qs(qs, timezone.now())
        return qs

    def catechisms_for_learning(self):
        """
        Return catechism objects decorated with tested_total and untested_total
        """
        statuses = self.catechism_qas_for_learning(None).select_related('version')

        # Already have enough info for untested_total
        catechisms = {}
        for s in statuses:
            catechism_id = s.version_id
            if catechism_id not in catechisms:
                catechism = s.version
                catechisms[catechism_id] = catechism
                catechism.untested_total = 0
            else:
                catechism = catechisms[catechism_id]
            catechism.untested_total += 1

        for c in catechisms.values():
            c.tested_total = c.qapairs.count() - c.untested_total

        return sorted(catechisms.values(), key=lambda c: c.full_name)

    def catechisms_for_revising(self):
        """
        Returns catechisms that need revising, decorated with needs_revising_total
        """
        statuses = self.catechism_qas_for_revising(None).select_related('version')
        catechisms = {}
        for s in statuses:
            catechism_id = s.version_id
            if catechism_id not in catechisms:
                catechism = s.version
                catechisms[catechism_id] = catechism
                catechism.needs_revising_total = 0
            else:
                catechism = catechisms[catechism_id]
            catechism.needs_revising_total += 1

        return sorted(catechisms.values(), key=lambda c: c.full_name)

    def clear_catechism_learning_queue(self, catechism_id):
        self.catechism_qas_for_learning_qs(catechism_id).delete()

    def get_all_tested_catechism_qas(self, catechism_id):
        return (self._catechism_qas_base_qs(catechism_id)
                .filter(memory_stage__gte=MemoryStage.TESTED)
                .order_by('text_order'))

    def verse_statuses_for_ref_and_version(self, reference, version_slug):
        return self.verse_statuses.filter(reference=reference,
                                          version__slug=version_slug,
                                          ignored=False)

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

    def passage_verse_sets_being_learnt_ids(self):
        """
        Returns a list of ids of passage VerseSets that are still being learnt
        (i.e. haven't all been tested yet).
        """
        return (self.verse_statuses
                .filter(verse_set__set_type=VerseSetType.PASSAGE,
                        ignored=False,
                        memory_stage__lt=MemoryStage.TESTED)
                .values_list('verse_set_id', flat=True).distinct())

    def verse_sets_chosen(self):
        """
        Returns a QuerySet of VerseSets that have been/are being learnt
        """
        ids = (self.verse_statuses
               .filter(ignored=False)
               .values_list('verse_set_id', flat=True).distinct())

        return VerseSet.objects.filter(id__in=ids).order_by('name')

    def which_verses_started(self, references):
        """
        Given a list of references, returns the ones that the user has started
        to learn.
        """
        return set(uvs.reference
                   for uvs in self.verse_statuses.filter(reference__in=references,
                                                         ignored=False,
                                                         memory_stage__gte=MemoryStage.TESTED))

    def which_in_learning_queue(self, references):
        """
        Given a list of references, returns the ones that are in the user's
        queue for learning.
        """
        return set(uvs.reference
                   for uvs in (self.bible_verse_statuses_for_learning_qs()
                               .filter(reference__in=references)))

    def passages_for_revising(self):
        statuses = self.verse_statuses.filter(verse_set__set_type=VerseSetType.PASSAGE,
                                              ignored=False,
                                              memory_stage__gte=MemoryStage.TESTED)\
                                      .select_related('verse_set')

        # If any of them need revising, we want to know about it:
        statuses = memorymodel.filter_qs(statuses, timezone.now())

        # However, we want to exclude those which have any verses in the set
        # still untested.
        statuses = statuses.exclude(verse_set__in=self.passage_verse_sets_being_learnt_ids())

        # We also need to know if group testing is on the cards, since that
        # allows for the possibility of splitting into sections for section
        # learning.

        uvs_list = list(statuses)  # Query 1
        verse_sets = set(uvs.verse_set for uvs in uvs_list)
        group_testing = dict((vs.id, True) for vs in verse_sets)
        all_statuses = self.verse_statuses.filter(verse_set__in=verse_sets)\
            .select_related('verse_set')

        all_statuses_list = list(all_statuses)  # Query 2

        # UVS instances will have different VerseSet instances attached,
        # even though the same VerseSet ID. Fix that up here:
        vs_d = {}
        for l in [uvs_list, all_statuses_list]:
            for uvs in l:
                if uvs.verse_set_id in vs_d:
                    uvs.verse_set = vs_d[uvs.verse_set_id]
                else:
                    vs_d[uvs.verse_set_id] = uvs.verse_set

        # Decorate with various extra things we want to show in dashboard:
        #  - next_section_verse_count
        #  - splittable
        #  - needs_testing_count
        #  - total_verse_count

        for vs in verse_sets:
            uvss = [uvs for uvs in all_statuses_list if uvs.verse_set_id == vs.id]
            self._set_needs_testing_override(uvss)
            next_section = self.get_next_section(uvss, vs, add_buffer=False)
            vs.next_section_verse_count = len(next_section)

        for uvs in all_statuses_list:
            vs = uvs.verse_set
            if not hasattr(vs, 'needs_testing_count'):
                uvs.verse_set.needs_testing_count = 0
                uvs.verse_set.total_verse_count = 0

            if uvs.needs_testing:
                uvs.verse_set.needs_testing_count += 1
            uvs.verse_set.total_verse_count += 1

        for uvs in all_statuses_list:
            if uvs.strength <= memorymodel.STRENGTH_FOR_GROUP_TESTING:
                group_testing[uvs.verse_set_id] = False

        vss = list(verse_sets)
        for vs in vss:
            vs.splittable = vs.breaks != "" and group_testing[vs.id]

        return sorted(vss, key=lambda vs: vs.name)

    def next_verse_due(self):
        try:
            # We need to exlude verses that are part of passage sets that are
            # still being learnt
            learning_sets_ids = self.passage_verse_sets_being_learnt_ids()

            return (self.verse_statuses
                    .filter(ignored=False,
                            next_test_due__isnull=False,
                            next_test_due__gte=timezone.now(),
                            strength__lt=memorymodel.LEARNT)
                    .exclude(verse_set__in=learning_sets_ids)
                    .order_by('next_test_due'))[0]
        except IndexError:
            return None

    def first_overdue_verse(self, now):
        try:
            return (self.verse_statuses
                    .filter(ignored=False,
                            next_test_due__isnull=False,
                            next_test_due__lt=now,
                            strength__lt=memorymodel.LEARNT)
                    .order_by('next_test_due'))[0]
        except IndexError:
            return None

    def verse_statuses_for_passage(self, verse_set_id):
        # Must be strictly in the bible order
        uvs_list = list(self.verse_statuses.filter(verse_set=verse_set_id,
                                                   ignored=False).order_by('text_order'))
        if len(uvs_list) == 0:
            return []

        self._set_needs_testing_override(uvs_list)
        return uvs_list

    def _set_needs_testing_override(self, uvs_list):
        if len(uvs_list) == 0:
            return
        min_strength = min(uvs.strength for uvs in uvs_list)
        if min_strength > memorymodel.STRENGTH_FOR_GROUP_TESTING:
            for uvs in uvs_list:
                uvs.needs_testing_override = True
        return uvs_list

    def get_next_section(self, uvs_list, verse_set, add_buffer=True):
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
        section_info = {}  # section idx: info dict
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
        for i, info in reversed(sorted(section_info.items())):
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

        retval = []
        if add_buffer:
            if section_num > 0:
                # Return a verse of context with 'needs_testing_override' being set
                # to False.
                context = sections[section_num - 1][-1]
                context.needs_testing_override = False
                retval.append(context)

        retval.extend(sections[section_num])

        return retval

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
        tested_sections = set()
        for i, section in enumerate(sections):
            if (any(uvs.needs_testing for uvs in section)):
                # Need this section.  If we didn't put last section in, and the
                # first verse in this section needs testing, we add the last verse
                # of the previous section (which by this logic does not need testing)
                # to provide some context and flow between the sections.
                if i > 0:
                    if i - 1 not in tested_sections and section[0].needs_testing:
                        to_test.append(sections[i - 1][-1])
                to_test.extend(section)
                tested_sections.add(i)

        return to_test

    def cancel_passage(self, verse_set_id):
        # For passages, the UserVerseStatuses may be already tested.
        # We don't want to lose that info, therefore set to 'ignored',
        # rather than delete() (unlike clear_bible_learning_queue)
        self.verse_statuses\
            .filter(verse_set=verse_set_id, ignored=False)\
            .update(ignored=True)

    def get_score_logs(self, from_datetime):
        if self.account_id is None:
            return []
        else:
            return self.account.get_score_logs(from_datetime)

    @property
    def scoring_enabled(self):
        if self.account_id is None:
            return False
        return True

    def available_bible_versions(self):
        if self.account_id is not None:
            if self.account.is_tester:
                return TextVersion.objects.bibles()
        return TextVersion.objects.bibles().filter(public=True)

    def get_dashboard_events(self, now=None):
        from events.models import Event
        return Event.objects.for_dashboard(now=now, account=self.account)

    def add_html_notice(self, notice):
        return self.notices.create(message_html=notice)

    def can_edit_verse_set(self, verse_set):
        if self.account_id is None:
            return False
        return self.account.can_edit_verse_set(verse_set)


class Notice(models.Model):
    for_identity = models.ForeignKey(Identity, related_name='notices')
    message_html = models.TextField()
    created = models.DateTimeField(default=timezone.now)
    seen = models.DateTimeField(default=None, null=True, blank=True)
    related_event = models.ForeignKey('events.Event', null=True, blank=True)

    def is_old(self):
        return (timezone.now() - self.created).days >= 2

    def __unicode__(self):
        return u"Notice %d for %r" % (self.id, self.for_identity)


def get_verse_started_running_streaks():
    """
    Returns a dictionary of {account_id: largest learning streak}
    """
    from learnscripture.utils.sqla import default_engine

    # We can get the beginning of running streaks like this -
    # all rows that don't have a row one day before them chronologically

    sql1 = """
SELECT
    DISTINCT accounts_identity.account_id, t1.d1 FROM
    (SELECT for_identity_id, date_trunc('day', first_seen AT TIME ZONE 'UTC') as d1
     FROM bibleverses_userversestatus
     WHERE first_seen is not NULL
           AND ignored = false
    ) t1
LEFT OUTER JOIN
    (SELECT for_identity_id, date_trunc('day', first_seen AT TIME ZONE 'UTC') as d2
     FROM bibleverses_userversestatus
     WHERE first_seen is not NULL
           AND ignored = false
    ) t2

  ON t1.d1 = t2.d2 + interval '1 day'
     AND t1.for_identity_id = t2.for_identity_id
INNER JOIN accounts_identity
  ON accounts_identity.id = t1.for_identity_id
     AND accounts_identity.account_id IS NOT NULL

WHERE t2.d2 IS NULL;

"""

    # Similarly, get end of running streaks like this:
    sql2 = sql1.replace(" + interval '1 day'",
                        " - interval '1 day'")

    starts = default_engine.execute(sql1).fetchall()
    ends = default_engine.execute(sql2).fetchall()

    # We've got results for all accounts, so need to split:
    def split(results):
        out = defaultdict(list)
        for i, d in results:
            out[i].append(d)
        for v in out.values():
            v.sort()
        return out

    start_dict = split(starts)
    end_dict = split(ends)
    interval_dict = defaultdict(list)

    # Now get can intervals by zipping starts and ends:
    for i in start_dict.keys():
        for start, end in zip(start_dict[i], end_dict[i]):
            interval_dict[i].append((end - start).days)

    return dict((i, max(intervals) + 1) for i, intervals in interval_dict.items())


def get_active_account_count(since_when, until_when):
    """
    Returns the number of accounts that have used the site in the time period.
    """
    # This isn't accurate is until_when is not now(), since UserVerseStatus is
    # overwritten. However, it doesn't matter too much, since we run this daily
    # and only had a small backlog of initial data to cope with.
    from bibleverses.models import UserVerseStatus
    return (UserVerseStatus.objects.
            filter(for_identity__account__isnull=False,
                   last_tested__lte=until_when,
                   last_tested__gt=since_when)
            .values('for_identity_id').distinct().count()
            )


def get_active_identity_count(since_when, until_when):
    # As above, but for all identities, not just those with accounts.
    from bibleverses.models import UserVerseStatus
    return (UserVerseStatus.objects.
            filter(last_tested__lte=until_when,
                   last_tested__gt=since_when)
            .values('for_identity_id').distinct().count()
            )


from accounts import hooks  # NOQA


def notify_all_accounts(html_message):
    for account in Account.objects.active().filter(identity__isnull=False).select_related('identity'):
        account.add_html_notice(html_message)
