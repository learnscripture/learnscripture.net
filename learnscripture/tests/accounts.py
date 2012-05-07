from __future__ import absolute_import

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import Account, SubscriptionType, ActionChange, Identity
from awards.models import AwardType
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
                                   email='test@test.com',
                                   subscription=SubscriptionType.PAID_UP)

        a.award_action_points("John 3:16", "This is John 3:16",
                              MemoryStage.TESTED,
                              ActionChange(old_strength=0.5, new_strength=0.6),
                              StageType.TEST, 0.75)
        self.assertEqual(a.total_score.points,
                         (4 * Scores.POINTS_PER_WORD * 0.75))


    def test_ace_awards(self):
        account = Account.objects.create(username='test',
                                         email='test@test.com',
                                         subscription=SubscriptionType.PAID_UP)
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
                                   email='test@test.com',
                                   subscription=SubscriptionType.PAID_UP)

        a.award_action_points("John 3:16", "This is John 3:16",
                              MemoryStage.TESTED,
                              ActionChange(old_strength=0.7, new_strength=0.99),
                              StageType.TEST, 0.9)
        self.assertEqual(a.total_score.points,
                         (4 * Scores.POINTS_PER_WORD * 0.9)
                         + (4 * Scores.POINTS_PER_WORD * Scores.VERSE_LEARNT_BONUS))


    def test_subscription_discount(self):
        # Main account
        a1 = Account.objects.create(username='test1',
                                    email='tes1t@test.com',
                                    subscription=SubscriptionType.PAID_UP,
                                    paid_until=timezone.now() - timedelta(1))
        i1 = Identity.objects.create(account=a1)


        # Free trial
        a2 = Account.objects.create(username='test2',
                                    email='test2@test.com',
                                    subscription=SubscriptionType.FREE_TRIAL)
        i2 = Identity.objects.create(account=a2)

        # Paid up, expired
        a3 = Account.objects.create(username='test3',
                                    email='test3@test.com',
                                    subscription=SubscriptionType.PAID_UP,
                                    paid_until=timezone.now() - timedelta(100)
                                    )
        i3 = Identity.objects.create(account=a3)

        # Paid up, current
        a4 = Account.objects.create(username='test4',
                                    email='test4@test.com',
                                    subscription=SubscriptionType.PAID_UP,
                                    paid_until=timezone.now() + timedelta(100)
                                    )
        i4 = Identity.objects.create(account=a4)

        # 0 referrers
        self.assertEqual(a1.subscription_discount(), Decimal('0.0'))

        # 1 referrer, on free trial
        i2.referred_by = a1
        i2.save()
        self.assertEqual(a1.subscription_discount(), Decimal('0.0'))

        # 1 referrer, paid up but expired
        i3.referred_by = a1
        i3.save()
        self.assertEqual(a1.subscription_discount(), Decimal('0.0'))

        # 1 referrer, paid up and current
        i4.referred_by = a1
        i4.save()
        self.assertEqual(a1.subscription_discount(), Decimal('0.10'))
