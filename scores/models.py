from datetime import timedelta

from django.db import connection
from django.db import models
from django.db.models import F, Sum
from django.utils import timezone

from learnscripture.datastructures import make_choices
from learnscripture.utils.db import dictfetchall

ScoreReason = make_choices('ScoreReason',
                           [(0, 'VERSE_TESTED', 'Verse tested'),
                            (1, 'VERSE_REVISED', 'Verse revised'),
                            (2, 'REVISION_COMPLETED', 'Revision completed'), # No longer used
                            (3, 'PERFECT_TEST_BONUS', 'Perfect!'),
                            (4, 'VERSE_LEARNT', 'Verse fully learnt'),
                            (5, 'EARNED_AWARD', 'Earned award'),
                            ])


class Scores(object):
    # Constants for scores. Duplicated in learn.js
    POINTS_PER_WORD = 20
    PERFECT_BONUS_FACTOR = 0.5
    VERSE_LEARNT_BONUS = 2


class ScoreLog(models.Model):
    account = models.ForeignKey('accounts.Account', related_name='score_logs')
    points = models.PositiveIntegerField()
    reason = models.PositiveSmallIntegerField(choices=ScoreReason.choice_list)
    accuracy = models.FloatField(null=True, blank=True)
    created = models.DateTimeField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
            TotalScore.objects.filter(account=self.account)\
                .update(points=F('points') + self.points)
        super(ScoreLog, self).save(*args, **kwargs)

    class Meta:
        ordering = ('-created',)

    def __repr__(self):
        return "<ScoreLog account=%s points=%s reason=%s created=%s>" % (
            self.account.email, self.points, self.get_reason_display(), self.created)


class TotalScore(models.Model):
    account = models.OneToOneField('accounts.Account', related_name='total_score')
    points = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)


def active_user_query(q):
    from learnscripture.utils.sqla import accounts_account as account
    return (q
            .where(account.c.is_active == True)
            )


def get_all_time_leaderboard(page, page_size, group=None):
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
                                 from_obj=totalscore.join(account)))
        .group_by(totalscore.c.account_id,
                  totalscore.c.points)
        .order_by(totalscore.c.points.desc())
        )

    if group is not None:
        account_ids = [a.id for a in group.members.all()]
        subq1 = subq1.where(account.c.id.in_(account_ids))

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


def get_leaderboard_since(since, page, page_size, group=None):
    # page is zero indexed

    # This uses a completely different strategy to get_all_time_leaderboard, and
    # only works if ScoreLogs haven't been cleared out for the relevant period.

    from learnscripture.utils.sqla import default_engine, accounts_account, scores_scorelog
    from sqlalchemy.sql import select
    from sqlalchemy.sql.functions import next_value
    from sqlalchemy.schema import Sequence
    from sqlalchemy.sql import func

    account = accounts_account
    scorelog = scores_scorelog

    sq = Sequence('rank_seq')

    subq1 = (
        active_user_query(select([scorelog.c.account_id,
                                  func.sum(scorelog.c.points).label('sum_points')],
                                 from_obj=scorelog.join(account)))
        .where(scorelog.c.created > since)
        .group_by(scorelog.c.account_id)
        )

    if group is not None:
        account_ids = [a.id for a in group.members.all()]
        subq1 = subq1.where(account.c.id.in_(account_ids))


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


def get_rank_all_time(total_score_obj):
    return TotalScore.objects.filter(
        points__gt=total_score_obj.points,
        account__is_active=True
        ).count() + 1


def get_rank_this_week(points_this_week):
    n = timezone.now()
    return ScoreLog.objects.filter(created__gt=n - timedelta(7))\
        .filter(account__is_active=True)\
        .values('account_id').annotate(sum_points=models.Sum('points'))\
        .filter(sum_points__gt=points_this_week).count() + 1


def get_number_of_distinct_hours_for_account_id(account_id):
    from learnscripture.utils.sqla import scores_scorelog, default_engine
    from sqlalchemy.sql import select, distinct, extract
    from sqlalchemy import func

    sq1 = select(
        [distinct(extract('hour', scores_scorelog.c.created)).label('hours')],
        scores_scorelog.c.account_id == account_id,
        from_obj=[scores_scorelog]
        ).alias()
    q1 = select([func.count(sq1.c.hours)],
                from_obj=sq1)

    return default_engine.execute(q1).fetchall()[0][0]
