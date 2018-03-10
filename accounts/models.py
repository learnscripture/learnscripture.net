import itertools
import math
import operator
from collections import OrderedDict, defaultdict
from datetime import timedelta
from functools import reduce

import attr
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.contrib.sites.shortcuts import get_current_site
from django.core import mail
from django.db import models
from django.template import loader
from django.utils import timezone
from django.utils.functional import cached_property

from accounts import memorymodel
from accounts.signals import (catechism_started, points_increase, scored_100_percent, verse_finished, verse_started,
                              verse_tested)
from bibleverses.languages import DEFAULT_LANGUAGE
from bibleverses.models import (InvalidVerseReference, MemoryStage, StageType, TextType, TextVersion, UserVerseStatus,
                                VerseSet, VerseSetType, get_passage_sections, normalized_verse_list_ref)
from bibleverses.signals import verse_set_chosen
from bibleverses.textutils import count_words
from learnscripture.datastructures import make_choices
from learnscripture.utils.cache import cache_results, clear_cache_results
from scores.models import ScoreReason, Scores, TotalScore

TestingMethod = make_choices('TestingMethod',
                             [('FULL_WORDS', 'FULL_WORDS', 'Type whole word - most thorough'),
                              ('FIRST_LETTER', 'FIRST_LETTER', 'Type first letter - faster'),
                              ('ON_SCREEN', 'ON_SCREEN', 'Choose from word list - recommended for'
                               ' handheld devices.' +
                               ' Only available for English translations'),
                              ])

THEMES = [('calm', 'Slate'),
          ('bubblegum', 'Bubblegum pink'),
          ('bubblegum2', 'Bubblegum green'),
          ('space', 'Space'),
          ]
THEME_FONTS = [
    ('calm', ['https://fonts.googleapis.com/css?family=Cuprum&subset=latin-ext']),
    ('bubblegum', ['https://fonts.googleapis.com/css?family=Short+Stack']),
    ('bubblegum2', ['https://fonts.googleapis.com/css?family=Short+Stack']),
    ('space', ['https://fonts.googleapis.com/css?family=Prosto+One']),
]
DEFAULT_THEME = 'calm'

DONT_NAG_NEW_USERS_FOR_MONEY_DAYS = 30

HeatmapStatsType = make_choices('HeatmapStatsType',
                                [('VERSES_STARTED', 'Items started'),
                                 ('VERSES_TESTED', 'Items tested'),
                                 ('COMBINED', 'Combined'),
                                 ])


# Account is separate from Identity to allow guest users to use the site fully
# without signing up.
#
# Everything related to learning verses is related to Identity.
# Social aspects and payment aspects are related to Account.
# Identity methods are the main interface for most business logic,
# and so sometimes they just delegate to Account methods.


SEND_REMINDERS_FOR = 30 * 3  # 3 months


class AccountManager(UserManager):
    def visible_for_account(self, account):
        qs = self.active()
        if account is None or not account.is_hellbanned:
            # Only hellbanned users see each other
            qs = qs.exclude(is_hellbanned=True)
        return qs

    def active(self):
        return self.get_queryset().filter(is_active=True)

    def send_reminders_to(self):
        return (self.active()
                .annotate(last_item_tested_on=models.Max('identity__verse_statuses__last_tested'))
                .filter(remind_after__gt=0,
                        email_bounced__isnull=True,
                        last_item_tested_on__gt=timezone.now() - timedelta(days=SEND_REMINDERS_FOR),
                        )
                )


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

    @property
    def default_language_code(self):
        return self.identity.default_language_code

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
        return (self.first_name.strip() + ' ' + self.last_name.strip()).strip()

    @property
    def recruited_by(self):
        return self.identity.referred_by

    def __str__(self):
        return self.username

    # Main business logic
    def award_action_points(self, localized_reference, language_code, text,
                            old_memory_stage, action_change,
                            action_stage, accuracy):
        if action_stage != StageType.TEST:
            return []

        action_logs = []
        word_count = count_words(text)
        max_points = word_count * Scores.points_per_word(language_code)
        if old_memory_stage >= MemoryStage.TESTED:
            reason = ScoreReason.VERSE_REVIEWED
        else:
            reason = ScoreReason.VERSE_TESTED
        points = max_points * accuracy
        action_logs.append(self.add_points(points, reason, accuracy=accuracy, localized_reference=localized_reference))

        if accuracy == 1:
            action_logs.append(self.add_points(points * Scores.PERFECT_BONUS_FACTOR,
                                               ScoreReason.PERFECT_TEST_BONUS,
                                               localized_reference=localized_reference,
                                               accuracy=accuracy))
            # At least one subscriber to scored_100_percent relies on action_logs
            # to be created in order to do job. In context of tests, this means
            # we have to send this signal after creating ActionLog
            scored_100_percent.send(sender=self)

        if (action_change.old_strength < memorymodel.LEARNT <= action_change.new_strength):
            action_logs.append(self.add_points(word_count * Scores.points_per_word(language_code) *
                                               Scores.VERSE_LEARNT_BONUS,
                                               ScoreReason.VERSE_LEARNT,
                                               localized_reference=localized_reference,
                                               accuracy=accuracy))
            verse_finished.send(sender=self)

        if action_stage == StageType.TEST and old_memory_stage < MemoryStage.TESTED:
            verse_started.send(sender=self)

        return action_logs

    def add_points(self, points, reason, accuracy=None, localized_reference=""):
        # Need to refresh 'total_score' each time
        points = math.floor(points)
        current_points = TotalScore.objects.get(account_id=self.id).points
        action_log = self.action_logs.create(points=points,
                                             reason=reason,
                                             localized_reference=localized_reference,
                                             accuracy=accuracy)
        # Change cached object to reflect DB, which has been
        # updated via a SQL UPDATE for max correctness.
        self.total_score.points = current_points + points
        points_increase.send(sender=self,
                             previous_points=current_points,
                             points_added=action_log.points)
        return action_log

    def get_action_logs(self, from_datetime, highest_id_seen=0):
        return (self.action_logs
                .filter(created__gte=from_datetime,
                        id__gt=highest_id_seen)
                .order_by('created')
                )

    @cached_property
    def points_all_time(self):
        return self.total_score.points

    @cached_property
    def points_this_week(self):
        n = timezone.now()
        val = self.action_logs.filter(created__gt=n - timedelta(7))\
            .aggregate(models.Sum('points'))['points__sum']
        return val if val is not None else 0

    def receive_payment(self, ipn_obj):
        if ipn_obj.mc_currency == settings.VALID_RECEIVE_CURRENCY:
            amount = ipn_obj.mc_gross
        elif ipn_obj.settle_currency == settings.VALID_RECEIVE_CURRENCY:
            amount = ipn_obj.settle_amount
        else:
            raise ValueError("Unrecognized currency")
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


def normalize_weighting(weights):
    if not weights:
        return
    max_weight = max(weights.values())
    for k, v in weights.items():
        weights[k] = v / max_weight


@cache_results(seconds=1200)
def account_get_friendship_weights(account_id):
    # We use groups to define possible friendships.
    account = Account.objects.get(id=account_id)
    weights = defaultdict(int)
    for group in account.groups.filter(count_for_friendships=True).prefetch_related('members'):
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

    # Normalize to 1
    normalize_weighting(weights)

    # We use 'following' in indicate definite friendships. Following is worth
    # more than any evidence from groups.
    for acc in account.following.all():
        weights[acc.id] += 1.5

    # Normalize again
    normalize_weighting(weights)

    # Give some weight to self, so user sees their own events.
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
    subject = "LearnScripture.net - donation received"
    mail.send_mail(subject, body, settings.SERVER_EMAIL, [account.email])


class ActionChange(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class IdentityManager(models.Manager):
    def get_queryset(self):
        return super(IdentityManager, self).get_queryset().select_related('default_bible_version', 'account')


# Most of business logic regarding verses is tied to Identity, for the sake of
# having somewhere to put it, and because most queries need to start
# 'identity.verse_statuses' so this may as well be 'self.verse_statuses'


class Identity(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, null=True, blank=True, default=None)
    date_created = models.DateTimeField(default=timezone.now)

    # Preferences
    default_bible_version = models.ForeignKey(TextVersion, on_delete=models.CASCADE,
                                              null=True, blank=True)
    desktop_testing_method = models.CharField(max_length=20,
                                              choices=TestingMethod.choice_list,
                                              default=TestingMethod.FULL_WORDS)
    touchscreen_testing_method = models.CharField(max_length=20,
                                                  choices=TestingMethod.choice_list,
                                                  default=TestingMethod.ON_SCREEN)
    enable_animations = models.BooleanField(blank=True, default=True)
    enable_sounds = models.BooleanField(blank=True, default=False)
    enable_vibration = models.BooleanField("Vibrate on mistakes", blank=True, default=True,
                                           help_text="Depends on device capabilities.")
    interface_theme = models.CharField(max_length=30, choices=THEMES,
                                       default=DEFAULT_THEME)
    referred_by = models.ForeignKey(Account, on_delete=models.CASCADE,
                                    null=True, default=None,
                                    blank=True,
                                    related_name='referrals')
    heatmap_default_stats_type = models.CharField(max_length=20,
                                                  choices=HeatmapStatsType.choice_list,
                                                  default=HeatmapStatsType.COMBINED)
    heatmap_default_show = models.BooleanField(default=True)

    pin_action_log_menu_large_screen = models.BooleanField(default=False)
    pin_action_log_menu_small_screen = models.BooleanField(default=False)
    pin_verse_options_menu_large_screen = models.BooleanField(default=False)
    seen_help_tour = models.BooleanField(default=False)

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

    def __str__(self):
        if self.account_id is None:
            return '<Identity %s>' % self.id
        else:
            return '<Identity %s: %s>' % (self.id, self.account)

    def __repr__(self):
        return str(self)

    @property
    def preferences_setup(self):
        return self.default_bible_version is not None

    @property
    def default_to_dashboard(self):
        return self.preferences_setup

    @property
    def default_language_code(self):
        # For now, just use this, make it a proper setting later.
        if self.default_bible_version is None:
            return DEFAULT_LANGUAGE.code
        else:
            return self.default_bible_version.language_code

    def add_verse_set(self, verse_set, version=None):
        """
        Adds the verses in a VerseSet to the user's UserVerseStatus objects,
        and returns the UserVerseStatus objects.
        """
        if version is None:
            version = self.default_bible_version
        language_code = version.language_code

        out = []

        vc_list = verse_set.verse_choices.all()
        existing_uvss = set(self.verse_statuses
                            .active()
                            .filter(verse_set=verse_set,
                                    version=version))

        uvss_dict = dict([(uvs.localized_reference, uvs) for uvs in existing_uvss])

        # Want to preserve order of verse_set, so iterate like this:
        for vc in vc_list:
            vc_localized_reference = vc.get_localized_reference(language_code)
            if vc_localized_reference in uvss_dict:
                # Save work - create_verse_status is expensive
                out.append(uvss_dict[vc_localized_reference])
            else:
                new_uvs = self.create_verse_status(vc_localized_reference, verse_set, version)
                if new_uvs is not None and new_uvs not in out:
                    out.append(new_uvs)

        verse_set_chosen.send(sender=verse_set, chosen_by=self.account)
        return out

    def add_verse_choice(self, localized_reference, version=None):
        if version is None:
            version = self.default_bible_version

        existing = list(self.verse_statuses
                        .active()
                        .filter(localized_reference=localized_reference,
                                verse_set__isnull=True))
        if existing:
            return existing[0]
        else:
            return self.create_verse_status(localized_reference, None, version)

    def add_catechism(self, catechism):
        """
        Add the QAPairs in a catechism to a user's UserVerseStatuses.
        """
        base_uvs_query = self.verse_statuses.filter(version=catechism)
        existing_uvss = base_uvs_query
        existing_refs = set(uvs.localized_reference for uvs in existing_uvss)
        # Some might be set to 'ignored'. Need to fix that.
        if any(uvs.ignored for uvs in existing_uvss):
            base_uvs_query.update(ignored=False)

        qapairs = catechism.qapairs.all().order_by('order')

        new_uvss = [
            UserVerseStatus(
                for_identity=self,
                localized_reference=qapair.localized_reference,
                text_order=qapair.order,
                version=catechism,
                added=timezone.now()
            )
            for qapair in qapairs if qapair.localized_reference not in existing_refs]
        UserVerseStatus.objects.bulk_create(new_uvss)
        return base_uvs_query.all().order_by('text_order')  # fresh QuerySet

    def record_verse_action(self, localized_reference, version_slug, stage_type, accuracy=None):
        """
        Records an action such as 'READ' or 'TESTED' against a verse.
        Returns an ActionChange object.
        """
        # We keep this separate from award_action_points because it needs
        # different info, and it is easier to test with its current API.

        s = self.verse_statuses.filter(localized_reference=localized_reference,
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

            # Learn.elm calculateNextTestDue uses the same logic as here to
            # indicate when a verse will be next seen. Changes should be synced.
            old_strength = s0.strength
            if s0.last_tested is None:
                time_elapsed = None
            else:
                time_elapsed = (now - s0.last_tested).total_seconds()
            new_strength = memorymodel.strength_estimate(old_strength, accuracy, time_elapsed)
            next_due = now + timedelta(seconds=memorymodel.next_test_due_after(new_strength))
            s.update(strength=new_strength,
                     last_tested=now,
                     next_test_due=next_due,
                     early_review_requested=False)

            # Sometimes we get to here with 'first_seen' still null,
            # so we fix it to keep our data making sense.
            s.filter(strength__gt=0, first_seen__isnull=True).update(first_seen=now)

            verse_tested.send(sender=self, verse=s0)
            if (s0.version.is_catechism and s0.text_order == 1 and
                    old_strength == 0.0 and
                    self.account_id is not None):
                catechism_started.send(self.account, catechism=s0.version)

            return ActionChange(old_strength=old_strength, new_strength=new_strength)

        if mem_stage == MemoryStage.SEEN:
            s.filter(first_seen__isnull=True).update(first_seen=now)
            return ActionChange()

    def award_action_points(self, localized_reference, language_code,
                            text, old_memory_stage, action_change,
                            action_stage, accuracy):
        if self.account_id is None:
            return []

        return self.account.award_action_points(localized_reference, language_code,
                                                text, old_memory_stage, action_change,
                                                action_stage, accuracy)

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
            refs = [uvs.localized_reference for uvs in uvs_list]
            for ref, text in version.get_text_by_localized_reference_bulk(refs).items():
                # Bibles only here
                texts[version_id, ref] = text
            for ref, qapair in version.get_qapairs_by_localized_reference_bulk(refs).items():
                # catechisms only here
                qapairs[version_id, ref] = qapair
            for ref, suggestions in version.get_suggestions_by_localized_reference_bulk(refs).items():
                # Bibles and catechsims here
                suggestion_d[version_id, ref] = suggestions

        # Assign texts back to uvs:
        for uvs in retval.values():
            text = texts.get((uvs.version_id, uvs.localized_reference), None)
            if text is not None:
                # Bible
                uvs.scoring_text = text
                uvs.title_text = uvs.localized_reference

            qapair = qapairs.get((uvs.version_id, uvs.localized_reference), None)
            if qapair is not None:
                # Catechism
                question, answer = qapair.question, qapair.answer
                uvs.scoring_text = answer
                uvs.title_text = uvs.localized_reference + ". " + question
            uvs.suggestions = suggestion_d.get((uvs.version_id, uvs.localized_reference), [])

        return retval

    def create_verse_status(self, localized_reference, verse_set, version):
        try:
            verse_list = version.get_verse_list(localized_reference)
        except InvalidVerseReference:
            # This can happen if Verse.missing==True for this version.
            return

        # text_order has to be specified in create since it is non-nullable
        text_order = verse_list[0].gapless_bible_verse_number

        # Merged verses: verse_list might have a different idea about what
        # localized_reference is. Also need to cope with Combo verses.
        localized_reference = normalized_verse_list_ref(version.language_code,
                                                        verse_list)

        # NB: we are exploiting the fact that multiple calls to
        # create_verse_status will get slightly increasing values of 'added',
        # allowing us to preserve order.
        uvs, new = self.verse_statuses.get_or_create(verse_set=verse_set,
                                                     localized_reference=localized_reference,
                                                     version=version,
                                                     defaults=dict(text_order=text_order,
                                                                   added=timezone.now()
                                                                   )
                                                     )

        dirty = False
        # See if we already have data for this verse + version, for the
        # case where the user started learning the verse standalone, not
        # as part of a verse set, or in a different verse set.
        same_verses = self.verse_statuses.filter(localized_reference=localized_reference,
                                                 version=version).exclude(id=uvs.id)

        if same_verses and new:
            # Use existing data:
            same_verse = same_verses[0]
            uvs.memory_stage = same_verse.memory_stage
            uvs.strength = same_verse.strength
            # If previous record was ignored, it may have been cancelled, so we
            # ignore 'added' since otherwise it will interfere with ordering if
            # this is added to learning queue.
            if not same_verse.ignored:
                uvs.added = same_verse.added
            uvs.first_seen = same_verse.first_seen
            uvs.last_tested = same_verse.last_tested
            uvs.next_test_due = same_verse.next_test_due
            uvs.early_review_requested = same_verse.early_review_requested
            dirty = True

        if uvs.ignored:
            uvs.ignored = False
            dirty = True

        if dirty:
            uvs.save()

        return uvs

    def cancel_learning(self, localized_references, version_slug):
        """
        Cancel learning some verses.

        Ignores VerseChoices that belong to passage sets.
        """
        # Not used for passages verse sets.
        qs = self.verse_statuses.filter(localized_reference__in=localized_references,
                                        version__slug=version_slug)
        qs = qs.exclude(verse_set__set_type=VerseSetType.PASSAGE)
        qs.update(ignored=True)

    def reset_progress(self, localized_reference, version_slug):
        # Sync with Learn.elm verseStatusResetProgress
        qs = self.verse_statuses.filter(localized_reference=localized_reference,
                                        version__slug=version_slug)

        # NB - we don't change 'first_seen', because this could destroy
        # someone's learning streak.
        qs.update(strength=0,
                  last_tested=None,
                  next_test_due=None,
                  memory_stage=MemoryStage.ZERO,
                  early_review_requested=False)

    def review_sooner(self, localized_reference, version_slug, review_after_seconds):
        # Could in theory do this with an update, but it is easier in Python and
        # the queryset likely only has one item in it.
        qs = self.verse_statuses.filter(localized_reference=localized_reference,
                                        version__slug=version_slug)
        for uvs in qs:
            last_tested = uvs.last_tested
            if last_tested is None:
                last_tested = timezone.now()
            uvs.next_test_due = last_tested + timedelta(seconds=review_after_seconds)
            uvs.early_review_requested = True
            uvs.save()

    def _dedupe_uvs_set(self, uvs_set):
        # dedupe instances with same ref and version
        retval = []
        seen_items = set()
        for uvs in uvs_set:
            if (uvs.localized_reference, uvs.version_id) in seen_items:
                continue
            seen_items.add((uvs.localized_reference, uvs.version_id))
            retval.append(uvs)
        return retval

    def _dedupe_uvs_set_distinguishing_verse_set(self, uvs_set):
        # Only dedupe multiple instances with same ref and verse_set==None
        retval = []
        seen_refs = set()
        for uvs in uvs_set:
            if uvs.verse_set_id is None:
                if uvs.localized_reference in seen_refs:
                    continue
                seen_refs.add(uvs.localized_reference)
            retval.append(uvs)
        return retval

    def verse_statuses_started(self):
        return (self.verse_statuses
                .active()
                .filter(strength__gt=0,
                        last_tested__isnull=False))

    def verses_started_count(self, started_since=None):
        from scores.models import get_verses_started_counts
        return get_verses_started_counts([self.id],
                                         started_since=started_since
                                         )[self.id]

    def verses_finished_count(self, finished_since=None):
        from scores.models import get_verses_finished_count
        return get_verses_finished_count(self.id, self.account_id, finished_since=finished_since)

    def bible_verse_statuses_for_reviewing(self):
        """
        Returns a list of UserVerseStatuses that need reviewing.
        """
        qs = (self.verse_statuses
              .filter(version__text_type=TextType.BIBLE)
              .needs_reviewing(timezone.now())
              # Don't include passages - we do those separately:
              .exclude(verse_set__set_type=VerseSetType.PASSAGE)
              .order_by('next_test_due', 'added')
              )
        return self._dedupe_uvs_set(qs)

    def bible_verse_statuses_for_learning_qs(self):
        qs = (self.verse_statuses
              .active()
              .filter(version__text_type=TextType.BIBLE,
                      memory_stage__lt=MemoryStage.TESTED)
              # Don't include passages - we do those separately:
              .exclude(verse_set__set_type=VerseSetType.PASSAGE)
              )
        return qs

    def bible_verse_statuses_for_learning(self, verse_set_id):
        """
        Returns a list of UserVerseStatuses that need learning.

        If verse_set_id is None, then all will be returned, otherwise the verse set
        specified in verse_set_id will be returned.
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
              .active()
              .filter(version__text_type=TextType.CATECHISM)
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

    def catechism_qas_for_reviewing(self, catechism_id):
        """
        Returns catechism QAs that are due for reviewing
        """
        return (self._catechism_qas_base_qs(catechism_id)
                .needs_reviewing(timezone.now()))

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

    def catechisms_for_reviewing(self):
        """
        Returns catechisms that need reviewing, decorated with needs_reviewing_total
        """
        statuses = self.catechism_qas_for_reviewing(None).select_related('version')
        catechisms = {}
        for s in statuses:
            catechism_id = s.version_id
            if catechism_id not in catechisms:
                catechism = s.version
                catechisms[catechism_id] = catechism
                catechism.needs_reviewing_total = 0
            else:
                catechism = catechisms[catechism_id]
            catechism.needs_reviewing_total += 1

        return sorted(catechisms.values(), key=lambda c: c.full_name)

    def clear_catechism_learning_queue(self, catechism_id):
        self.catechism_qas_for_learning_qs(catechism_id).delete()

    def get_all_tested_catechism_qas(self, catechism_id):
        return (self._catechism_qas_base_qs(catechism_id)
                .filter(memory_stage__gte=MemoryStage.TESTED)
                .order_by('text_order'))

    def verse_statuses_for_ref_and_version(self, localized_reference, version_slug):
        return (self.verse_statuses
                .active()
                .filter(localized_reference=localized_reference,
                        version__slug=version_slug))

    def passages_for_learning(self, extra_stats=True):
        """
        Retrieves a list of ChosenVerseSet objects of 'passage' type that need
        more initial learning.
        If 'extra_stats==True', they are decorated with 'untested_total' and 'tested_total' attributes.
        """
        statuses = (self.verse_statuses
                    .active()
                    .filter(verse_set__set_type=VerseSetType.PASSAGE,
                            memory_stage__lt=MemoryStage.TESTED)
                    .select_related('verse_set', 'version'))
        chosen_verse_sets = {}

        # We already have info needed for untested_total
        for s in statuses:
            cvs = ChosenVerseSet(version=s.version,
                                 verse_set=s.verse_set)
            cvs_id = cvs.id
            if cvs_id not in chosen_verse_sets:
                chosen_verse_sets[cvs_id] = cvs
                if extra_stats:
                    cvs.untested_total = 0
            else:
                cvs = chosen_verse_sets[cvs_id]
            if extra_stats:
                cvs.untested_total += 1

        if extra_stats:
            now = timezone.now()

            # We need two additional queries per ChosenVerseSet for tested_total
            # and needs_review_total.
            for cvs in chosen_verse_sets.values():
                stats_qs = self.verse_statuses.filter(verse_set=cvs.verse_set,
                                                      version=cvs.version)

                cvs.tested_total = stats_qs.tested().count()
                cvs.needs_review_total = stats_qs.needs_reviewing(now).count()

        return sorted(list(chosen_verse_sets.values()), key=lambda c: c.sort_key)

    def verse_sets_chosen(self):
        """
        Returns a list of ChosenVerseSets that have been/are being learnt
        """
        pairs = (self.verse_statuses
                 .active()
                 .filter(verse_set__isnull=False)
                 .values_list('verse_set_id', 'version_id')
                 .distinct())
        if len(pairs) == 0:
            return []
        vs_ids, tv_ids = list(zip(*pairs))
        versions = {tv.id: tv
                    for tv in TextVersion.objects.filter(id__in=tv_ids)}
        verse_sets = {vs.id: vs
                      for vs in VerseSet.objects.filter(id__in=vs_ids)}
        retval = [ChosenVerseSet(version=versions[tv_id],
                                 verse_set=verse_sets[vs_id])
                  for vs_id, tv_id in pairs]
        retval.sort(key=lambda c: c.sort_key)
        return retval

    def which_verses_started(self, localized_references, version):
        """
        Given a list of localized_references, returns the ones that the user has started
        to learn.
        """
        return set(uvs.localized_reference
                   for uvs in (self.verse_statuses
                               .tested()
                               .filter(localized_reference__in=localized_references,
                                       version=version)))

    def which_in_learning_queue(self, localized_references, version):
        """
        Given a list of localized references, returns the ones that are in the user's
        queue for learning.
        """
        return set(uvs.localized_reference
                   for uvs in (self.bible_verse_statuses_for_learning_qs()
                               .filter(localized_reference__in=localized_references,
                                       version=version)))

    def passages_for_reviewing_and_learning(self):
        """
        Returns a tuple:
        (list of ChosenVerseSet items for passage VerseSets that need reviewing,
         list of ChosenVerseSet items for passage VerseSets that need learning).
        Both have extra info needed by dashboard.
        """
        learning_sets = self.passages_for_learning()
        learning_verse_set_ids = set(cvs.id for cvs in learning_sets)
        # We need the 'learning' sets in order to calculate the 'reviewing'
        # sets correctly, because we exclude the former from the latter.
        # We also always use these two return values at the same time.
        # So it makes sense to return them together.
        statuses = (self.verse_statuses
                    .active()
                    .filter(verse_set__set_type=VerseSetType.PASSAGE))

        # If any of them need reviewing, we want to know about it:
        statuses_for_review = (statuses
                               .reviewable()
                               .needs_reviewing(timezone.now())
                               .select_related('verse_set', 'version'))

        # We also want to exclude those which have any verses in the set still
        # untested, but this is easiest done as a second pass after retrieving.

        # Query 1
        chosen_verse_sets = set(ChosenVerseSet(verse_set=uvs.verse_set,
                                               version=uvs.version)
                                for uvs in statuses_for_review)

        # Decorate with various extra things we want to show in dashboard:
        #  - next_section_verse_count
        #  - splittable
        #  - needs_testing_count
        #  - total_verse_count

        # Remove things that are still in initial learning phase
        chosen_verse_set_list = [
            cvs for cvs in chosen_verse_sets if cvs.id not in learning_verse_set_ids
        ]

        # We need the complete list of UVSs for each verse set to get
        # the rest of the info correct.
        all_uvss = (statuses
                    .filter(verse_set__in=[cvs.verse_set for cvs in chosen_verse_set_list])
                    .order_by('text_order'))
        uvss_for_cvs = defaultdict(list)
        for uvs in all_uvss:
            uvss_for_cvs[uvs.verse_set_id, uvs.version_id].append(uvs)

        for cvs in chosen_verse_set_list:
            uvss = uvss_for_cvs[cvs.verse_set.id, cvs.version.id]
            self._set_needs_testing_override(uvss)
            next_section = self.get_next_section(uvss, cvs.verse_set, add_buffer=False)
            cvs.next_section_verse_count = len(next_section)

            cvs.needs_testing_count = 0
            cvs.group_testing = True
            cvs.total_verse_count = len(uvss)

            for uvs in uvss:
                if uvs.needs_testing:
                    cvs.needs_testing_count += 1

                if uvs.strength <= memorymodel.STRENGTH_FOR_GROUP_TESTING:
                    cvs.group_testing = False

            cvs.splittable = cvs.verse_set.breaks != "" and cvs.group_testing

        reviewing_sets = sorted(list(chosen_verse_set_list), key=lambda c: c.sort_key)
        return (reviewing_sets, learning_sets)

    def next_verse_due(self):

        exclude_ids = []
        cvss = self.passages_for_learning(extra_stats=False)
        if cvss:
            # We need to exlude verses that are part of passage sets that are
            # still being learnt, because those are pushed back from being
            # 'reviewed' while the rest of the passage is in initial learning.
            exclude_ids = list(reduce(operator.or_,
                                      [self.verse_statuses
                                       .filter(verse_set=cvs.verse_set, version=cvs.version)
                                       for cvs in cvss]).values_list('id', flat=True))

        return (self.verse_statuses
                .reviewable()
                .needs_reviewing_in_future(timezone.now())
                .exclude(id__in=exclude_ids)
                .order_by('next_test_due')
                .first())

    def first_overdue_verse(self, now):
        return (self.verse_statuses
                .needs_reviewing(now)
                .order_by('next_test_due')
                .first())

    def verse_statuses_for_passage(self, verse_set_id, version_id):
        # Must be strictly in the bible order
        uvs_list = list(self.verse_statuses
                        .active()
                        .filter(verse_set=verse_set_id,
                                version=version_id)
                        .order_by('text_order'))
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
                if uvs.strength < memorymodel.LEARNT:
                    uvs.needs_testing_override = True

    def get_next_section(self, uvs_list, verse_set, add_buffer=True):
        """
        Given a UVS list and a VerseSet, get the items in uvs_list
        which are the next section to review.
        """
        # We don't track which was the last 'section' learnt, and we can't,
        # since the user can give up at any point.  We therefore use heuristics
        # to work out which should be the next section.

        if verse_set.breaks == '' or len(uvs_list) == 0:
            return uvs_list

        uvs_list.sort(key=lambda u: u.text_order)
        language_code = uvs_list[0].version.language_code
        # First split into sections according to the specified breaks
        sections = get_passage_sections(language_code, uvs_list, verse_set.breaks)

        # Aim: get the section containing the least recently tested verse
        # that needs to be tested.
        last_tested_by_section = {}  # section idx: min_last_tested
        section_to_test = None
        for i, section in enumerate(sections):
            if any(uvs.last_tested is None for uvs in section):
                # This section has not been tested fully, so make it the next
                # section.
                section_to_test = i
                break
            else:
                last_tested = [uvs.last_tested for uvs in section
                               if uvs.needs_testing_individual]
                if last_tested:
                    last_tested_by_section[i] = min(last_tested)

        if section_to_test is None:
            all_last_tested = last_tested_by_section.values()
            if all_last_tested:
                overall_min_last_tested = min(all_last_tested)
                section_to_test = [i for i, min_last_tested in last_tested_by_section.items()
                                   if min_last_tested == overall_min_last_tested][0]
            else:
                # No section has a verse that needs testing.
                # So we just choose 0 arbitrarily
                section_to_test = 0

        retval = []
        if add_buffer:
            if section_to_test > 0:
                # Return a verse of context with 'needs_testing_override' being set
                # to False.
                context = sections[section_to_test - 1][-1]
                context.needs_testing_override = False
                retval.append(context)

        retval.extend(sections[section_to_test])

        return retval

    def slim_passage_for_reviewing(self, uvs_list, verse_set):
        """
        Uses breaks defined for the verse set to slim a passage
        down if not all verses need testing.
        """

        if verse_set.breaks == '' or len(uvs_list) == 0:
            return uvs_list

        uvs_list.sort(key=lambda u: u.text_order)
        language_code = uvs_list[0].version.language_code
        # First split into sections according to the specified breaks
        sections = get_passage_sections(language_code, uvs_list, verse_set.breaks)

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

    def cancel_passage(self, verse_set_id, version_id):
        # For passages, the UserVerseStatuses may be already tested.
        # We don't want to lose that info, therefore set to 'ignored',
        # rather than delete() (unlike clear_bible_learning_queue)
        self.verse_statuses.filter(verse_set=verse_set_id,
                                   version_id=version_id,
                                   ignored=False).update(ignored=True)

    def get_action_logs(self, from_datetime, highest_id_seen=0):
        if self.account_id is None:
            return []
        else:
            return self.account.get_action_logs(from_datetime,
                                                highest_id_seen=highest_id_seen)

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
        return Event.objects.for_dashboard(self.default_language_code, now=now, account=self.account)

    def add_html_notice(self, notice):
        return self.notices.create(message_html=notice)

    def can_edit_verse_set(self, verse_set):
        if self.account_id is None:
            return False
        return self.account.can_edit_verse_set(verse_set)


class Notice(models.Model):
    for_identity = models.ForeignKey(Identity, on_delete=models.CASCADE,
                                     related_name='notices')
    message_html = models.TextField()
    created = models.DateTimeField(default=timezone.now)
    seen = models.DateTimeField(default=None, null=True, blank=True)
    related_event = models.ForeignKey('events.Event', on_delete=models.CASCADE,
                                      null=True, blank=True)

    def is_old(self):
        return (timezone.now() - self.created).days >= 2

    def __str__(self):
        return "Notice %d for %r" % (self.id, self.for_identity)


@attr.s(hash=False)
class ChosenVerseSet(object):
    verse_set = attr.ib()
    version = attr.ib()

    def __hash__(self):
        return hash((self.verse_set.id, self.version.id))

    @property
    def sort_key(self):
        return (self.verse_set.name, self.version.short_name)

    @property
    def id(self):
        return "{0}-{1}".format(self.verse_set.id, self.version.id)


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
    # This isn't accurate if until_when is not now(), since
    # UserVerseStatus.last_tested is overwritten every time a verse is tested.
    # However, it doesn't matter too much, since we run this daily and only had
    # a small backlog of initial data to cope with.
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


def notify_all_accounts(html_message):
    for account in Account.objects.active().filter(identity__isnull=False).select_related('identity'):
        account.add_html_notice(html_message)


def notify_all_identities(html_message):
    for identity in Identity.objects.all().select_related(None):
        identity.add_html_notice(html_message)
