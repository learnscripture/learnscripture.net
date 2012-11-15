from __future__ import absolute_import

from django.core.urlresolvers import reverse
from django.test import TestCase

from accounts.models import Account, Identity


class UserStatsTests(TestCase):

    def test_get(self):
        a1 = Account.objects.create(username='testuser1',
                                    email='test2@test.com')
        i1 = Identity.objects.create(account=a1)

        resp = self.client.get(reverse('user_stats', args=(a1.username,)))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, a1.username)

    def test_get_inactive(self):
        a1 = Account.objects.create(username='testuser1',
                                    email='test2@test.com',
                                    is_active=False)
        i1 = Identity.objects.create(account=a1)

        resp = self.client.get(reverse('user_stats', args=(a1.username,)))
        self.assertEqual(resp.status_code, 404)
