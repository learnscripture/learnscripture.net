from __future__ import absolute_import

from datetime import timedelta
from decimal import Decimal

from django.db.models import F
from django.test import TestCase
from django.utils import timezone

from accounts.models import Account, ActionChange, Identity
from awards.models import AwardType, Award
from bibleverses.models import MemoryStage, StageType
from events.models import Event, EventType
from scores.models import Scores, ScoreReason


class AccountTests(TestCase):
    def test_password(self):
        acc = Account()
        acc.set_password('mypassword')
        self.assertTrue(acc.check_password('mypassword'))
        self.assertFalse(acc.check_password('123'))


    def test_award_action_points_revision(self):
        a = Account.objects.create(username='test',
                                   email='test@test.com')

        a.award_action_points("John 3:16", "This is John 3:16",
                              MemoryStage.TESTED,
                              ActionChange(old_strength=0.5, new_strength=0.6),
                              StageType.TEST, 0.75)
        self.assertEqual(a.total_score.points,
                         (4 * Scores.POINTS_PER_WORD * 0.75))

    def test_points_events(self):
        a = Account.objects.create(username='test',
                                   email='test@test.com')
        def score():
            a.award_action_points("John 3:16", "This is John 3:16",
                                  MemoryStage.TESTED,
                                  ActionChange(old_strength=0.5, new_strength=0.6),
                                  StageType.TEST, 0.75)

        # One rep of score() gives 60 points.
        # When we cross over 1000 (repetition 17) we should get an event
        for i in range(1, 20):
            score()
            self.assertEqual(Event.objects.filter(event_type=EventType.POINTS_MILESTONE).count(),
                             0 if i < 17 else 1)

    def test_ace_awards(self):
        account = Account.objects.create(username='test',
                                         email='test@test.com')
        identity = Identity.objects.create(account=account)

        self.assertEqual(account.awards.filter(award_type=AwardType.ACE).count(),
                         0)

        def score(accuracy):
            account.award_action_points("John 3:16", "This is John 3:16",
                                        MemoryStage.TESTED,
                                        ActionChange(old_strength=0.5, new_strength=0.6),
                                        StageType.TEST, accuracy)

        score(0.75)
        # Check no 'ACE' award
        self.assertEqual(account.awards.filter(award_type=AwardType.ACE).count(),
                         0)

        score(1.0)

        # Check level 1
        self.assertEqual(account.awards.filter(award_type=AwardType.ACE, level=1).count(),
                         1)

        score(1.0)

        # Check level 2
        self.assertEqual(account.awards.filter(award_type=AwardType.ACE, level=2).count(),
                         1)

        # Negative check: record one at less than 100% to break streak
        score(0.9)
        # 3 more
        score(1)
        score(1)
        score(1)

        # Negative check level 3
        self.assertEqual(account.awards.filter(award_type=AwardType.ACE, level=3).count(),
                         0)
        # 4th one:
        score(1)
        self.assertEqual(account.awards.filter(award_type=AwardType.ACE, level=3).count(),
                         1)


        # Check 'Event' created
        self.assertTrue(Event.objects.filter(event_type=EventType.AWARD_RECEIVED).count() > 1)


    def test_award_action_points_fully_learnt(self):
        a = Account.objects.create(username='test',
                                   email='test@test.com')
        Identity.objects.create(account=a)

        a.award_action_points("John 3:16", "This is John 3:16",
                              MemoryStage.TESTED,
                              ActionChange(old_strength=0.7, new_strength=0.99),
                              StageType.TEST, 0.9)
        self.assertEqual(a.total_score.points,
                         (4 * Scores.POINTS_PER_WORD * 0.9)
                         + (4 * Scores.POINTS_PER_WORD * Scores.VERSE_LEARNT_BONUS))


    def test_addict_award(self):
        import awards.tasks
        account = Account.objects.create(username='test',
                                         email='test@test.com')
        identity = Identity.objects.create(account=account)

        def score():
            # We simulate testing over time by moving previous data back an hour
            account.score_logs.update(created=F('created') - timedelta(hours=1))
            account.award_action_points("John 3:16", "This is John 3:16",
                                        MemoryStage.TESTED,
                                        ActionChange(old_strength=0.5, new_strength=0.6),
                                        StageType.TEST, 0.5)

        for i in range(0, 24):
            score()

            # Simulate the cronjob that runs
            awards.tasks.give_all_addict_awards()

            self.assertEqual(account.awards.filter(award_type=AwardType.ADDICT).count(),
                             0 if i < 23 else 1)


    def test_champion_awards(self):
        a1 = Account.objects.create(username='test1',
                                    email='test1@test.com')
        a2 = Account.objects.create(username='test2',
                                    email='test2@test.com')

        Identity.objects.create(account=a1)
        Identity.objects.create(account=a2)

        a1.add_points(200, ScoreReason.VERSE_TESTED, accuracy=1.0)
        a2.add_points(100, ScoreReason.VERSE_TESTED, accuracy=1.0)

        # Simulate the cronjob that runs
        self.do_give_champion_awards()

        self.assertEqual(a1.awards
                         .filter(award_type=AwardType.REIGNING_WEEKLY_CHAMPION)
                         .count(),
                         1)
        self.assertEqual(a2.awards
                         .filter(award_type=AwardType.REIGNING_WEEKLY_CHAMPION)
                         .count(),
                         0)
        self.assertEqual(a1.awards
                         .filter(award_type=AwardType.WEEKLY_CHAMPION)
                         .count(),
                         1)
        self.assertEqual(a2.awards
                         .filter(award_type=AwardType.WEEKLY_CHAMPION)
                         .count(),
                         0)

        # Make a2 the leader
        a2.add_points(200, ScoreReason.VERSE_TESTED, accuracy=1.0)

        # Simulate the cronjob that runs
        self.do_give_champion_awards()

        # a1 should have lost 'REIGNING_WEEKLY_CHAMPION', but kept 'WEEKLY_CHAMPION'
        self.assertEqual(a1.awards
                         .filter(award_type=AwardType.REIGNING_WEEKLY_CHAMPION)
                         .count(),
                         0)
        self.assertEqual(a2.awards
                         .filter(award_type=AwardType.REIGNING_WEEKLY_CHAMPION)
                         .count(),
                         1)
        self.assertEqual(a1.awards
                         .filter(award_type=AwardType.WEEKLY_CHAMPION)
                         .count(),
                         1)
        self.assertEqual(a2.awards
                         .filter(award_type=AwardType.WEEKLY_CHAMPION)
                         .count(),
                         1)


        # Should have a 'lost award' notice
        self.assertEqual(a1.identity.notices.filter(message_html__contains="You've lost").count(),
                         1)

        # Should be a 'lost award' notice
        self.assertEqual(Event.objects.filter(message_html__contains="lost <").count(),
                         1)


        # Some time passes:
        Award.objects.update(created=F('created') - timedelta(days=10))

        self.do_give_champion_awards()

        # Should have level 2
        self.assertEqual([a.level for a in a2.awards
                          .filter(award_type=AwardType.WEEKLY_CHAMPION)
                          .order_by('level')],
                         [1, 2, 3])

    def do_give_champion_awards(self):
        import awards.tasks
        awards.tasks.give_champion_awards.delay(hellbanned=False)
        awards.tasks.give_champion_awards.delay(hellbanned=True)

    def test_champion_awards_hellbanned(self):
        """Test the logic of hellbanned champion awards."""
        # hellbanned user inhabit their own private reality. So if they get to
        # the top of a leaderboard it should appear to them that they have the
        # champion award. But not to non-hellbanned users, who see the real
        # champion, even if they have less points.

        # And the non-hellbanned user 
        a1 = Account.objects.create(username='test1',
                                    email='test1@test.com')
        a2 = Account.objects.create(username='test2',
                                    email='test2@test.com')
        a3 = Account.objects.create(username='test3',
                                    email='test3@test.com',
                                    is_hellbanned=True)

        Identity.objects.create(account=a1)
        Identity.objects.create(account=a2)
        Identity.objects.create(account=a3)

        a1.add_points(200, ScoreReason.VERSE_TESTED, accuracy=1.0)
        a2.add_points(100, ScoreReason.VERSE_TESTED, accuracy=1.0)
        a3.add_points(300, ScoreReason.VERSE_TESTED, accuracy=1.0)

        # Simulate the cronjob that runs
        self.do_give_champion_awards()

        self.assertEqual(a1.awards
                         .filter(award_type=AwardType.REIGNING_WEEKLY_CHAMPION)
                         .count(),
                         1)
        self.assertEqual(a2.awards
                         .filter(award_type=AwardType.REIGNING_WEEKLY_CHAMPION)
                         .count(),
                         0)
        self.assertEqual(a3.awards
                         .filter(award_type=AwardType.REIGNING_WEEKLY_CHAMPION)
                         .count(),
                         1)

        self.assertEqual(a1.awards
                         .filter(award_type=AwardType.WEEKLY_CHAMPION)
                         .count(),
                         1)
        self.assertEqual(a2.awards
                         .filter(award_type=AwardType.WEEKLY_CHAMPION)
                         .count(),
                         0)
        self.assertEqual(a3.awards
                         .filter(award_type=AwardType.WEEKLY_CHAMPION)
                         .count(),
                         1)

        a1.add_points(200, ScoreReason.VERSE_TESTED, accuracy=1.0)

        self.do_give_champion_awards()
        # a3 is now behind, should have lost REIGNING_WEEKLY_CHAMPION
        self.assertEqual(a3.awards
                         .filter(award_type=AwardType.REIGNING_WEEKLY_CHAMPION)
                         .count(),
                         0)

        a3.add_points(1000, ScoreReason.VERSE_TESTED, accuracy=1.0)

        self.do_give_champion_awards()
        # a3 is ahead (as far as a3 can see)
        self.assertEqual(a3.awards
                         .filter(award_type=AwardType.REIGNING_WEEKLY_CHAMPION)
                         .count(),
                         1)

        # but a1 is ahead, as far as a1 can see
        self.assertEqual(a1.awards
                         .filter(award_type=AwardType.REIGNING_WEEKLY_CHAMPION)
                         .count(),
                         1)
