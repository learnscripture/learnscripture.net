from django_functest import FuncBaseMixin

from .base import FullBrowserTest, WebTestBase


class FollowTestsBase(FuncBaseMixin):
    def test_follow_unfollow(self):
        identity1, account1 = self.create_account(username="famous_person")
        identity2, account2 = self.create_account(username="a_fan")

        self.login(account2)
        self.get_url("user_stats", account1.username)

        self.submit("#id-follow-btn", wait_for_reload=False)
        self.assertEqual(list(account2.following.all()), [account1])
        self.assertEqual(list(account1.followers.all()), [account2])

        self.submit("#id-unfollow-btn", wait_for_reload=False)
        self.assertEqual(list(account2.following.all()), [])
        self.assertEqual(list(account1.followers.all()), [])


class FollowTestsFB(FollowTestsBase, FullBrowserTest):
    pass


class FollowTestsWT(FollowTestsBase, WebTestBase):
    pass
