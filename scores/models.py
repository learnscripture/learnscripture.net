"""
Records of user scores and actions.

ActionLog is used for scores and for various things like calculating
streaks and awards.
TotalScore is a summary used for all time scores.

"""

import uuid
from datetime import timedelta

from django.db import models
from django.db.models import F
from django.utils import timezone

from bibleverses import languages


# See also Learn.elm which copies definition
class ScoreReason(models.IntegerChoices):
    VERSE_FIRST_TESTED = 0, "Verse first tested"
    VERSE_REVIEWED = 1, "Verse reviewed"
    REVISION_COMPLETED = 2, "Review completed"  # No longer used
    PERFECT_TEST_BONUS = 3, "Perfect!"
    VERSE_LEARNED = 4, "Verse fully learned"
    EARNED_AWARD = 5, "Earned award"


class Scores:
    # Constants for scores. Duplicated in learn.js
    PERFECT_BONUS_FACTOR = 0.5
    VERSE_LEARNED_BONUS = 2

    # This is based on a comparison of the number of words in a typical Bible
    # translation for each language:
    #
    # - NET for English     751460
    # - TCL02 for Turkish   448155
    # - SV-RJ for Dutch     770099
    # - RVG for Spanish     712554
    #
    # such that learning the same number of verses should get you the same
    # number of points (roughly).

    # Number of words in a text can be found by doing:

    # >>> from bibleverses.textutils import split_into_words
    # >>> text = TextVersion.objects.get(short_name='...')
    # >>> sum([len(split_into_words(v.text_saved)) for v in text.verse_set.filter(missing=False, merged_into__isnull=True)])

    # Then do: 751460 / words_in_bible * 20

    _LANGUAGE_POINTS_PER_WORD = {
        languages.LANG.EN: 20,
        languages.LANG.TR: 34,
        languages.LANG.NL: 19,
        languages.LANG.ES: 21,
    }

    @classmethod
    def points_per_word(cls, language_code):
        return cls._LANGUAGE_POINTS_PER_WORD[language_code]


class ActionLog(models.Model):
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="action_logs")
    points = models.PositiveIntegerField()
    reason = models.PositiveSmallIntegerField(choices=ScoreReason.choices)
    localized_reference = models.CharField(max_length=255, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    created = models.DateTimeField(db_index=True)
    award = models.OneToOneField("awards.Award", null=True, blank=True, on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created = timezone.now()
            self.update_total_score(self.points)
        super().save(*args, **kwargs)

    def update_total_score(self, by_points):
        TotalScore.objects.filter(account=self.account).update(points=F("points") + by_points)

    def delete(self, **kwargs):
        retval = super().delete(**kwargs)
        self.update_total_score(-self.points)
        return retval

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return f"<ActionLog {self.id}>"

    def __repr__(self):
        return f"<ActionLog account={self.account.username} points={self.points} reason={self.get_reason_display()} localized_reference={self.localized_reference} award={self.award} created={self.created}>"


class TotalScore(models.Model):
    account = models.OneToOneField("accounts.Account", on_delete=models.CASCADE, related_name="total_score")
    points = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return f"<TotalScore {self.points}>"


def active_user_query(q, hellbanned_mode):
    from learnscripture.utils.sqla import accounts_account as account

    retval = q.where(account.c.is_active == True)  # noqa
    if not hellbanned_mode:
        retval = retval.where(account.c.is_hellbanned != True)  # noqa
    return retval


def leaderboard_group_filter(q, hellbanned_mode, group):
    from learnscripture.utils.sqla import accounts_account

    if group is not None:
        members = group.members.all()
        if not hellbanned_mode:
            members = members.exclude(is_hellbanned=True)
        account_ids = [a.id for a in members]
        q = q.where(accounts_account.c.id.in_(account_ids))
    return q


def get_all_time_leaderboard(hellbanned_mode, from_item, page_size, group=None):
    # page is zero indexed

    from sqlalchemy.schema import Sequence
    from sqlalchemy.sql import select
    from sqlalchemy.sql.functions import next_value

    from learnscripture.utils.sqla import accounts_account, default_engine, scores_totalscore

    account = accounts_account
    totalscore = scores_totalscore

    sequence_name = f"rank_seq_{uuid.uuid4().hex}"
    sq = Sequence(sequence_name)

    subq1 = (
        active_user_query(
            select([totalscore.c.account_id, totalscore.c.points], from_obj=totalscore.join(account)), hellbanned_mode
        )
        .group_by(totalscore.c.account_id, totalscore.c.points)
        .order_by(totalscore.c.points.desc())
    )

    subq1 = leaderboard_group_filter(subq1, hellbanned_mode, group)
    subq1 = subq1.alias()

    q1 = (
        select([subq1.c.account_id, subq1.c.points, next_value(sq).label("rank")], from_obj=subq1)
        .limit(page_size)
        .offset(from_item)
    )

    default_engine.execute(f"CREATE TEMPORARY SEQUENCE {sequence_name};")
    results = default_engine.execute(q1).fetchall()
    default_engine.execute(f"DROP SEQUENCE {sequence_name};")
    return [{"account_id": r[0], "points": r[1], "rank": r[2]} for r in results]


def get_leaderboard_since(since, hellbanned_mode, from_item, page_size, group=None):
    # page is zero indexed

    # This uses a completely different strategy to get_all_time_leaderboard,
    # relying on ActionLog
    from sqlalchemy.schema import Sequence
    from sqlalchemy.sql import func, select
    from sqlalchemy.sql.functions import next_value

    from learnscripture.utils.sqla import accounts_account, default_engine, scores_actionlog

    account = accounts_account
    actionlog = scores_actionlog

    sequence_name = f"rank_seq_{uuid.uuid4().hex}"
    sq = Sequence(sequence_name)

    subq1 = (
        active_user_query(
            select(
                [actionlog.c.account_id, sum_points := func.sum(actionlog.c.points).label("sum_points")],
                from_obj=actionlog.join(account),
            ),
            hellbanned_mode,
        )
        .where(actionlog.c.created > since)
        .group_by(actionlog.c.account_id)
    )

    subq1 = leaderboard_group_filter(subq1, hellbanned_mode, group)

    subq1 = subq1.order_by(sum_points.desc())
    subq1 = subq1.alias()

    q1 = (
        select(
            [
                subq1.c.account_id,
                subq1.c.sum_points.label("points"),
                next_value(sq).label("rank"),
            ],
            from_obj=subq1,
        )
        .limit(page_size)
        .offset(from_item)
    )

    default_engine.execute(f"CREATE TEMPORARY SEQUENCE {sequence_name};")
    results = default_engine.execute(q1).fetchall()
    default_engine.execute(f"DROP SEQUENCE {sequence_name};")
    return [{"account_id": r[0], "points": r[1], "rank": r[2]} for r in results]


def get_number_of_distinct_hours_for_account_id(account_id):
    from sqlalchemy import func
    from sqlalchemy.sql import distinct, extract, select

    from learnscripture.utils.sqla import default_engine, scores_actionlog

    sq1 = select(
        [distinct(extract("hour", scores_actionlog.c.created)).label("hours")],
        scores_actionlog.c.account_id == account_id,
        from_obj=[scores_actionlog],
    ).alias()
    q1 = select([func.count(sq1.c.hours)], from_obj=sq1)

    return default_engine.execute(q1).fetchall()[0][0]


def _add_zeros(vals):
    retval = []
    old_date = None
    for d, c in vals:
        if old_date is not None:
            for i in range(1, (d - old_date).days):
                retval.append((old_date + timedelta(days=i), 0))
        retval.append((d, c))
        old_date = d
    return retval


def get_verses_started_counts(identity_ids, started_since=None):
    from sqlalchemy import func
    from sqlalchemy.sql import and_, select

    from bibleverses.models import MemoryStage
    from learnscripture.utils.sqla import bibleverses_userversestatus, default_engine

    # The important points about this complex query are:
    #
    # * grouping 'duplicate' UserVerseStatus rows i.e. ones for the same
    #   localized_reference and text.
    # * use of `internal_reference_list` to count combo/merged verse
    #   for their full value.

    if len(identity_ids) == 0:
        return {}

    uvs = bibleverses_userversestatus
    q1 = (
        select(
            [uvs.c.for_identity_id],
            and_(
                uvs.c.ignored == False,  # noqa:E712
                uvs.c.memory_stage >= MemoryStage.TESTED,
                uvs.c.for_identity_id.in_(identity_ids),
                *([uvs.c.first_seen > started_since] if started_since is not None else []),
            ),
        ).group_by(uvs.c.for_identity_id, func.unnest(uvs.c.internal_reference_list), uvs.c.version_id)
    ).alias()
    q2 = select([q1.c.for_identity_id, func.count()]).group_by(q1.c.for_identity_id)

    vals = {i: c for (i, c) in default_engine.execute(q2).fetchall()}
    return {i: vals.get(i, 0) for i in identity_ids}


def get_verses_started_per_day(identity_id):
    from sqlalchemy import func
    from sqlalchemy.sql import and_, select

    from learnscripture.utils.sqla import bibleverses_userversestatus, default_engine

    day_col = func.date_trunc("day", bibleverses_userversestatus.c.first_seen).label("day")

    q1 = (
        select(
            [day_col],
            and_(
                bibleverses_userversestatus.c.for_identity_id == identity_id,
                bibleverses_userversestatus.c.first_seen != None,  # noqa:E711
                bibleverses_userversestatus.c.ignored == False,  # noqa:E712
            ),
            from_obj=bibleverses_userversestatus,
        ).group_by(
            day_col,
            func.unnest(bibleverses_userversestatus.c.internal_reference_list),
            bibleverses_userversestatus.c.version_id,
        )
    ).alias()

    q2 = select([q1.c.day, func.count()], from_obj=q1).order_by(q1.c.day).group_by(q1.c.day)

    vals = [(d.date(), c) for (d, c) in default_engine.execute(q2).fetchall()]
    # Now we need to add zeros for the missing dates
    return _add_zeros(vals)


def get_verses_tested_per_day(account_id):
    from sqlalchemy import func
    from sqlalchemy.sql import and_, select

    from learnscripture.utils.sqla import default_engine, scores_actionlog

    day_col = func.date_trunc("day", scores_actionlog.c.created).label("day")
    q1 = (
        select(
            [day_col, func.count(day_col)],
            and_(
                scores_actionlog.c.account_id == account_id,
                scores_actionlog.c.reason.in_([ScoreReason.VERSE_FIRST_TESTED, ScoreReason.VERSE_REVIEWED]),
            ),
        )
        .order_by(day_col)
        .group_by(day_col)
    )

    vals = [(d.date(), c) for (d, c) in default_engine.execute(q1).fetchall()]
    return _add_zeros(vals)


def get_verses_finished_count(identity_id, finished_since=None):
    from sqlalchemy import func
    from sqlalchemy.sql import and_, select

    from accounts.memorymodel import MM
    from bibleverses.models import MemoryStage
    from learnscripture.utils.sqla import (
        accounts_identity,
        bibleverses_userversestatus,
        default_engine,
        scores_actionlog,
    )

    uvs = bibleverses_userversestatus
    from_table = uvs
    filters = and_(
        uvs.c.ignored == False,  # noqa:E712
        uvs.c.memory_stage >= MemoryStage.TESTED,
        uvs.c.strength >= MM.LEARNED,
        uvs.c.for_identity_id == identity_id,
    )
    if finished_since is not None:
        # Don't have needed info in UVS (should really fix this), have to join
        # to scores_actionlog
        from_table = from_table.join(accounts_identity, uvs.c.for_identity_id == accounts_identity.c.id).join(
            scores_actionlog,
            and_(
                scores_actionlog.c.account_id == accounts_identity.c.account_id,
                scores_actionlog.c.localized_reference == uvs.c.localized_reference,
            ),
        )
        filters = and_(
            filters, scores_actionlog.c.reason == ScoreReason.VERSE_LEARNED, scores_actionlog.c.created > finished_since
        )
    q1 = (
        select([func.unnest(uvs.c.internal_reference_list), uvs.c.version_id], filters, from_obj=from_table).group_by(
            func.unnest(uvs.c.internal_reference_list), uvs.c.version_id
        )
    ).alias()
    q2 = select([func.count()], from_obj=q1)
    return default_engine.execute(q2).fetchall()[0][0]
