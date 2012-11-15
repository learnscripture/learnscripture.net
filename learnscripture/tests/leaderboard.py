from __future__ import absolute_import

from django.core.urlresolvers import reverse
from django.test import TestCase

from accounts.models import Account, Identity
from scores.models import ScoreReason

from .base import UsesSQLAlchemyBase

class LeaderboardTests(UsesSQLAlchemyBase):

    def setUp(self):
        a1 = Account.objects.create(username='testuser1',
                                    email='test2@test.com')
        i1 = Identity.objects.create(account=a1)
        a1.add_points(100, ScoreReason.VERSE_TESTED)
        a2 = Account.objects.create(username='testuser2',
                                    email='test2@test.com',
                                    is_active=False)
        i2 = Identity.objects.create(account=a2)
        a2.add_points(50, ScoreReason.VERSE_TESTED)
        self.a1 = a1
        self.a2 = a2

    def test_get(self):
        resp = self.client.get(reverse('leaderboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.a1.username)
        self.assertNotContains(resp, self.a2.username)

    def test_get_thisweek(self):
        resp = self.client.get(reverse('leaderboard'), {'thisweek':'1'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.a1.username)
        self.assertNotContains(resp, self.a2.username)
