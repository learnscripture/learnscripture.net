"""
Records of user scores and actions.

ActionLog is used for scores and for various things like calculating
streaks and awards.
TotalScore is a summary used for all time scores.

"""
from datetime import timedelta

from django.db import models
from django.db.models import F
from django.utils import timezone

from bibleverses import languages
from learnscripture.datastructures import make_choices

# See also Learn.elm which copies definition
ScoreReason = make_choices('ScoreReason',
                           [(0, 'VERSE_TESTED', 'Verse tested'),
                            (1, 'VERSE_REVIEWED', 'Verse reviewed'),
                            (2, 'REVISION_COMPLETED', 'Review completed'),  # No longer used
                            (3, 'PERFECT_TEST_BONUS', 'Perfect!'),
                            (4, 'VERSE_LEARNT', 'Verse fully learnt'),
                            (5, 'EARNED_AWARD', 'Earned award'),
                            ])


class Scores(object):
    # Constants for scores. Duplicated in learn.js
    PERFECT_BONUS_FACTOR = 0.5
    VERSE_LEARNT_BONUS = 2

    # This is based on a comparison of the number of words in a typical Bible
    # translation for each language:
    #
    # - NET for English
    # - TCL02 for Turkish
    #
    # such that learning the same number of verses should get you the same
    # number of points (roughly).
    _LANGUAGE_POINTS_PER_WORD = {
        languages.LANGUAGE_CODE_EN: 20,
        languages.LANGUAGE_CODE_TR: 34,
    }

    @classmethod
    def points_per_word(cls, language_code):
        return cls._LANGUAGE_POINTS_PER_WORD[language_code]


class ActionLog(models.Model):
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE,
                                related_name='action_logs')
    points = models.PositiveIntegerField()
    reason = models.PositiveSmallIntegerField(choices=ScoreReason.choice_list)
    localized_reference = models.CharField(max_length=255, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    created = models.DateTimeField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
            TotalScore.objects.filter(account=self.account)\
                .update(points=F('points') + self.points)
        super(ActionLog, self).save(*args, **kwargs)

    class Meta:
        ordering = ('-created',)

    def __repr__(self):
        return "<ActionLog account=%s points=%s reason=%s localized_reference=%s created=%s>" % (
            self.account.username, self.points, self.get_reason_display(), self.localized_reference, self.created)


class TotalScore(models.Model):
    account = models.OneToOneField('accounts.Account', on_delete=models.CASCADE,
                                   related_name='total_score')
    points = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)


def active_user_query(q, hellbanned_mode):
    from learnscripture.utils.sqla import accounts_account as account
    retval = (q
              .where(account.c.is_active == True)  # noqa
              )
    if not hellbanned_mode:
        retval = (retval
                  .where(account.c.is_hellbanned != True)  # noqa
                  )
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


def get_all_time_leaderboard(hellbanned_mode, page, page_size, group=None):
    # page is zero indexed

    from learnscripture.utils.sqla import default_engine, accounts_account, scores_totalscore
    from sqlalchemy.sql import select
    from sqlalchemy.sql.functions import next_value
    from sqlalchemy.schema import Sequence

    account = accounts_account
    totalscore = scores_totalscore

    sq = Sequence('rank_seq')

    subq1 = (
        active_user_query(select([totalscore.c.account_id, totalscore.c.points],
                                 from_obj=totalscore.join(account)),
                          hellbanned_mode)
        .group_by(totalscore.c.account_id,
                  totalscore.c.points)
        .order_by(totalscore.c.points.desc())
    )

    subq1 = leaderboard_group_filter(subq1, hellbanned_mode, group)
    subq1 = subq1.alias()

    q1 = (select([subq1.c.account_id,
                 subq1.c.points,
                 next_value(sq).label('rank')],
                 from_obj=subq1
                 )
          .limit(page_size)
          .offset(page * page_size)
          )

    default_engine.execute("CREATE TEMPORARY SEQUENCE rank_seq;")
    results = default_engine.execute(q1).fetchall()
    default_engine.execute("DROP SEQUENCE rank_seq;")
    return [{'account_id': r[0], 'points': r[1], 'rank': r[2]}
            for r in results]


def get_leaderboard_since(since, hellbanned_mode, page, page_size, group=None):
    # page is zero indexed

    # This uses a completely different strategy to get_all_time_leaderboard,
    # relying on ActionLog
    from learnscripture.utils.sqla import default_engine, accounts_account, scores_actionlog
    from sqlalchemy.sql import select
    from sqlalchemy.sql.functions import next_value
    from sqlalchemy.schema import Sequence
    from sqlalchemy.sql import func

    account = accounts_account
    actionlog = scores_actionlog

    sq = Sequence('rank_seq')

    subq1 = (
        active_user_query(select([actionlog.c.account_id,
                                  func.sum(actionlog.c.points).label('sum_points')],
                                 from_obj=actionlog.join(account)),
                          hellbanned_mode)
        .where(actionlog.c.created > since)
        .group_by(actionlog.c.account_id)
    )

    subq1 = leaderboard_group_filter(subq1, hellbanned_mode, group)

    subq1 = subq1.order_by(subq1.c.sum_points.desc())
    subq1 = subq1.alias()

    q1 = (
        select([subq1.c.account_id,
                subq1.c.sum_points.label('points'),
                next_value(sq).label('rank'),
                ],
               from_obj=subq1)
        .limit(page_size)
        .offset(page * page_size)
    )

    default_engine.execute("CREATE TEMPORARY SEQUENCE rank_seq;")
    results = default_engine.execute(q1).fetchall()
    default_engine.execute("DROP SEQUENCE rank_seq;")
    return [{'account_id': r[0], 'points': r[1], 'rank': r[2]}
            for r in results]


def get_number_of_distinct_hours_for_account_id(account_id):
    from learnscripture.utils.sqla import scores_actionlog, default_engine
    from sqlalchemy.sql import select, distinct, extract
    from sqlalchemy import func

    sq1 = select(
        [distinct(extract('hour', scores_actionlog.c.created)).label('hours')],
        scores_actionlog.c.account_id == account_id,
        from_obj=[scores_actionlog]
    ).alias()
    q1 = select([func.count(sq1.c.hours)],
                from_obj=sq1)

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
    from bibleverses.models import MemoryStage
    from learnscripture.utils.sqla import bibleverses_userversestatus, default_engine
    from sqlalchemy.sql import select, and_
    from sqlalchemy import func

    # The important point about this complex query is that
    # it groups 'duplicate' UserVerseStatus rows i.e. ones
    # for the same localized_reference and text.

    # It returns results for all identities, because this is used sometimes.

    if len(identity_ids) == 0:
        return {}

    uvs = bibleverses_userversestatus
    q1 = (select([uvs.c.for_identity_id],
                 and_(uvs.c.ignored == False,  # noqa
                      uvs.c.memory_stage >= MemoryStage.TESTED,
                      uvs.c.for_identity_id.in_(identity_ids),
                      *([uvs.c.first_seen > started_since]
                        if started_since is not None else []))
                 )
          .group_by(uvs.c.for_identity_id,
                    uvs.c.localized_reference,
                    uvs.c.version_id)
          ).alias()
    q2 = (select([q1.c.for_identity_id, func.count()])
          .group_by(q1.c.for_identity_id))

    vals = {i: c for (i, c) in default_engine.execute(q2).fetchall()}
    return {i: vals.get(i, 0) for i in identity_ids}


def get_verses_started_per_day(identity_id):
    from learnscripture.utils.sqla import bibleverses_userversestatus, default_engine
    from sqlalchemy.sql import select, and_
    from sqlalchemy import func

    day_col = func.date_trunc('day', bibleverses_userversestatus.c.first_seen).label('day')

    q1 = (select([day_col],
                 and_(bibleverses_userversestatus.c.for_identity_id == identity_id,
                      bibleverses_userversestatus.c.first_seen != None,  # noqa
                      bibleverses_userversestatus.c.ignored == False,  # noqa
                      ),
                 from_obj=bibleverses_userversestatus
                 )
          .group_by(day_col,
                    bibleverses_userversestatus.c.localized_reference,
                    bibleverses_userversestatus.c.version_id)
          ).alias()

    q2 = (select([q1.c.day, func.count()],
                 from_obj=q1)
          .order_by(q1.c.day)
          .group_by(q1.c.day)
          )

    vals = [(d.date(), c) for (d, c) in default_engine.execute(q2).fetchall()]
    # Now we need to add zeros for the missing dates
    return _add_zeros(vals)


def get_verses_tested_per_day(account_id):
    from learnscripture.utils.sqla import scores_actionlog, default_engine
    from sqlalchemy.sql import select, and_
    from sqlalchemy import func

    day_col = func.date_trunc('day', scores_actionlog.c.created).label('day')
    q1 = (select([day_col,
                  func.count(day_col)],
                 and_(scores_actionlog.c.account_id == account_id,
                      scores_actionlog.c.reason.in_([ScoreReason.VERSE_TESTED,
                                                    ScoreReason.VERSE_REVIEWED])
                      )
                 )
          .order_by(day_col)
          .group_by(day_col)
          )

    vals = [(d.date(), c) for (d, c) in default_engine.execute(q1).fetchall()]
    return _add_zeros(vals)


def get_verses_finished_count(identity_id, account_id, finished_since=None):
    from accounts.memorymodel import MM
    from bibleverses.models import MemoryStage
    from learnscripture.utils.sqla import bibleverses_userversestatus, default_engine, scores_actionlog
    from sqlalchemy.sql import select, and_
    from sqlalchemy import func

    if finished_since is None:
        uvs = bibleverses_userversestatus
        q1 = (select([uvs.c.localized_reference, uvs.c.version_id],
                     and_(uvs.c.ignored == False,  # noqa
                          uvs.c.memory_stage >= MemoryStage.TESTED,
                          uvs.c.strength >= MM.LEARNT,
                          uvs.c.for_identity_id == identity_id,
                          ),
                     from_obj=uvs
                     )
              .group_by(uvs.c.localized_reference,
                        uvs.c.version_id)
              ).alias()
        q2 = (select([func.count()],
                     from_obj=q1))

        return default_engine.execute(q2).fetchall()[0][0]
    else:
        # Using ActionLog is less accurate, but the only reasonably accurate way
        # we have to track the verses fully learnt since in a given time period,
        # as UserVerseStatus doesn't have that info.
        q = (select([func.count()],
                    and_(scores_actionlog.c.account_id == account_id,
                         scores_actionlog.c.reason == ScoreReason.VERSE_LEARNT,
                         scores_actionlog.c.created > finished_since)))
        return default_engine.execute(q).fetchall()[0][0]
