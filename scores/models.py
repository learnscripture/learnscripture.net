
from django.db import models
from django.db.models import F
from django.utils import timezone

from learnscripture.datastructures import make_choices

ScoreReason = make_choices('ScoreReason',
                           [(0, 'VERSE_TESTED', 'Verse tested'),
                            (1, 'VERSE_REVISED', 'Verse revised'),
                            (2, 'REVISION_COMPLETED', 'Revision completed'),
                            (3, 'PERFECT_TEST_BONUS', 'Perfect!'),
                            (4, 'VERSE_LEARNT', 'Verse fully learnt'),
                            ])


class Scores(object):
    # Constants for scores. Duplicated in learn.js
    POINTS_PER_WORD = 10
    REVISION_BONUS_FACTOR = 2
    PERFECT_BONUS_FACTOR = 0.5
    REVISION_COMPLETE_BONUS_FACTOR = 1
    VERSE_LEARNT_BONUS = 5


class ScoreLog(models.Model):
    account = models.ForeignKey('accounts.Account', related_name='score_logs')
    points = models.PositiveIntegerField()
    reason = models.PositiveSmallIntegerField(choices=ScoreReason.choice_list)
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


def get_all_time_leaderboard(page, page_size):
    # page is zero indexed

    sql = """
SELECT
  accounts_account.username,
  points,
  rank() OVER (ORDER BY points DESC)
FROM
  scores_totalscore INNER JOIN accounts_account
  ON scores_totalscore.account_id = accounts_account.id
LIMIT %s
OFFSET %s
"""
    from django.db import connection
    cursor = connection.cursor()


    offset = page * page_size
    print page_size, offset

    cursor.execute(sql, [page_size, offset])

    return dictfetchall(cursor)


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]
