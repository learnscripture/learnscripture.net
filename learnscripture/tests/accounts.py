from __future__ import absolute_import

from django.test import TestCase

from accounts.models import Account, SubscriptionType, ActionChange
from bibleverses.models import MemoryStage, StageType
from scores.models import Scores, ScoreReason


class AccountTests(TestCase):
    def test_password(self):
        acc = Account()
        acc.set_password('mypassword')
        self.assertTrue(acc.check_password('mypassword'))
        self.assertFalse(acc.check_password('123'))


    def test_award_action_points_revision(self):
        a = Account.objects.create(username='test',
                                   email='test@test.com',
                                   subscription=SubscriptionType.PAID_UP)

        a.award_action_points("John 3:16", "This is John 3:16",
                              MemoryStage.TESTED,
                              ActionChange(old_strength=0.5, new_strength=0.6),
                              StageType.TEST, 0.75)
        self.assertEqual(a.total_score.points,
                         (4 * Scores.POINTS_PER_WORD * 0.75))


    def test_award_action_points_fully_learnt(self):
        a = Account.objects.create(username='test',
                                   email='test@test.com',
                                   subscription=SubscriptionType.PAID_UP)

        a.award_action_points("John 3:16", "This is John 3:16",
                              MemoryStage.TESTED,
                              ActionChange(old_strength=0.8, new_strength=0.99),
                              StageType.TEST, 0.9)
        self.assertEqual(a.total_score.points,
                         (4 * Scores.POINTS_PER_WORD * 0.9)
                         + (4 * Scores.POINTS_PER_WORD * Scores.VERSE_LEARNT_BONUS))

