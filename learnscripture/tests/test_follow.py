from .base import FullBrowserTest


class FollowTestsFB(FullBrowserTest):
    def test_follow_unfollow(self):
        identity1, account1 = self.create_account(username="famous_person")
        identity2, account2 = self.create_account(username="a_fan")

        self.login(account2)
        self.get_url("user_stats", account1.username)

        self.click("#id-follow-btn")
        self.wait_for_ajax()
        self.assertEqual(list(account2.following.all()), [account1])

        self.assertEqual(list(account1.followers.all()), [account2])

        self.click("#id-unfollow-btn")
        self.wait_for_ajax()
        self.assertEqual(list(account2.following.all()), [])

        self.assertEqual(list(account1.followers.all()), [])
