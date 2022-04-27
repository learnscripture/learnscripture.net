from django.urls import reverse

from accounts.models import Account, Identity
from learnscripture.tests.base import TestBase


class UserStatsTests(TestBase):
    def test_get(self):
        a1 = Account.objects.create(username="testuser1", email="test2@test.com")
        Identity.objects.create(account=a1)

        resp = self.client.get(reverse("user_stats", args=(a1.username,)))
        assert resp.status_code == 200
        self.assertContains(resp, a1.username)

    def test_get_inactive(self):
        a1 = Account.objects.create(username="testuser1", email="test2@test.com", is_active=False)
        Identity.objects.create(account=a1)

        resp = self.client.get(reverse("user_stats", args=(a1.username,)))
        assert resp.status_code == 404
