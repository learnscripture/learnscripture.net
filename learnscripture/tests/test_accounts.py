import re
from datetime import timedelta

from django.core import mail
from django.db.models import F
from django.urls import reverse
from six.moves.urllib.parse import ParseResult, urlparse

from accounts.models import Account, ActionChange
from awards.models import AwardType
from bibleverses.languages import LANG
from bibleverses.models import MemoryStage, StageType
from events.models import Event, EventType
from learnscripture.forms import AccountSetPasswordForm
from scores.models import Scores

from .base import AccountTestMixin, FullBrowserTest, TestBase, WebTestBase


class SignupTestsBase(AccountTestMixin):
    def test_signup(self):
        username = self.create_account_interactive()
        assert Account.objects.filter(username=username).exists()
        self.assertTextPresent("Account created")


class SignupTestsWT(SignupTestsBase, WebTestBase):
    pass


class SignupTestsFB(SignupTestsBase, FullBrowserTest):
    pass


class AccountTests(AccountTestMixin, TestBase):
    maxDiff = None

    def test_password(self):
        acc = Account()
        acc.set_password("mypassword")
        assert acc.check_password("mypassword")
        assert not acc.check_password("123")

    def test_award_action_points_revision(self):
        a = Account.objects.create(username="test", email="test@test.com")

        a.award_action_points(
            "John 3:16",
            LANG.EN,
            "This is John 3:16",
            MemoryStage.TESTED,
            ActionChange(old_strength=0.5, new_strength=0.6),
            StageType.TEST,
            0.75,
        )
        assert a.total_score.points == (4 * Scores.points_per_word(LANG.EN) * 0.75)

    def test_points_events(self):
        _, a = self.create_account()

        def score():
            a.award_action_points(
                "John 3:16",
                LANG.EN,
                "This is John 3:16",
                MemoryStage.TESTED,
                ActionChange(old_strength=0.5, new_strength=0.6),
                StageType.TEST,
                0.75,
            )

        # One rep of score() gives 60 points.
        # When we cross over 1000 (repetition 17) we should get an event
        for i in range(1, 20):
            score()
            assert Event.objects.filter(event_type=EventType.POINTS_MILESTONE).count() == (0 if i < 17 else 1)

    def test_ace_awards(self):
        _, account = self.create_account()

        assert account.awards.filter(award_type=AwardType.ACE).count() == 0

        def score(accuracy):
            account.award_action_points(
                "John 3:16",
                LANG.EN,
                "This is John 3:16",
                MemoryStage.TESTED,
                ActionChange(old_strength=0.5, new_strength=0.6),
                StageType.TEST,
                accuracy,
            )

        score(0.75)
        # Check no 'ACE' award
        assert account.awards.filter(award_type=AwardType.ACE).count() == 0

        score(1.0)

        # Check level 1
        assert account.awards.filter(award_type=AwardType.ACE, level=1).count() == 1

        score(1.0)

        # Check level 2
        assert account.awards.filter(award_type=AwardType.ACE, level=2).count() == 1

        # Negative check: record one at less than 100% to break streak
        score(0.9)
        # 3 more
        score(1)
        score(1)
        score(1)

        # Negative check level 3
        assert account.awards.filter(award_type=AwardType.ACE, level=3).count() == 0
        # 4th one:
        score(1)
        assert account.awards.filter(award_type=AwardType.ACE, level=3).count() == 1

        # Check 'Event' created
        assert Event.objects.filter(event_type=EventType.AWARD_RECEIVED).count() > 1

        # Check notices
        assert [m.message_html for m in account.identity.notices.order_by("created")] == [
            '<img src="/static/img/awards/award_ACE_level_1_50.png"> You\'ve earned a new badge: <a href="/user/t%C3%ABst1/">Ace - level 1</a>. Points bonus: 1,000. <span class="broadcast" data-link="/user/t%C3%ABst1/" data-picture="/static/img/awards/award_ACE_level_1_100.png" data-award-id="{}" data-award-level="1" data-award-name="Ace - level 1" data-account-username="tëst1" data-caption="I just earned a badge: Ace - level 1">Tell people: <a data-twitter-link><i class="icon-twitter"></i> Twitter</a></span>'.format(
                account.awards.get(award_type=AwardType.ACE, level=1).id
            ),
            '<img src="/static/img/awards/award_ACE_level_2_50.png"> You\'ve levelled up on one of your badges: <a href="/user/t%C3%ABst1/">Ace - level 2</a>. Points bonus: 2,000. <span class="broadcast" data-link="/user/t%C3%ABst1/" data-picture="/static/img/awards/award_ACE_level_2_100.png" data-award-id="{}" data-award-level="2" data-award-name="Ace - level 2" data-account-username="tëst1" data-caption="I just earned a badge: Ace - level 2">Tell people: <a data-twitter-link><i class="icon-twitter"></i> Twitter</a></span>'.format(
                account.awards.get(award_type=AwardType.ACE, level=2).id
            ),
            '<img src="/static/img/awards/award_ACE_level_3_50.png"> You\'ve levelled up on one of your badges: <a href="/user/t%C3%ABst1/">Ace - level 3</a>. Points bonus: 4,000. <span class="broadcast" data-link="/user/t%C3%ABst1/" data-picture="/static/img/awards/award_ACE_level_3_100.png" data-award-id="{}" data-award-level="3" data-award-name="Ace - level 3" data-account-username="tëst1" data-caption="I just earned a badge: Ace - level 3">Tell people: <a data-twitter-link><i class="icon-twitter"></i> Twitter</a></span>'.format(
                account.awards.get(award_type=AwardType.ACE, level=3).id
            ),
        ]

    def test_award_action_points_fully_learned(self):
        _, a = self.create_account()

        a.award_action_points(
            "John 3:16",
            LANG.EN,
            "This is John 3:16",
            MemoryStage.TESTED,
            ActionChange(old_strength=0.7, new_strength=0.99),
            StageType.TEST,
            0.9,
        )
        assert a.total_score.points == (4 * Scores.points_per_word(LANG.EN) * 0.9) + (
            4 * Scores.points_per_word(LANG.EN) * Scores.VERSE_LEARNED_BONUS
        )

    def test_addict_award(self):
        import awards.tasks

        _, account = self.create_account()

        def score():
            # We simulate testing over time by moving previous data back an hour
            account.action_logs.update(created=F("created") - timedelta(hours=1))
            account.award_action_points(
                "John 3:16",
                LANG.EN,
                "This is John 3:16",
                MemoryStage.TESTED,
                ActionChange(old_strength=0.5, new_strength=0.6),
                StageType.TEST,
                0.5,
            )

        for i in range(0, 24):
            score()

            # Simulate the cronjob that runs
            awards.tasks.give_all_addict_awards()

            assert account.awards.filter(award_type=AwardType.ADDICT).count() == (0 if i < 23 else 1)

    def test_friendship_weights(self):
        from .test_groups import create_group

        _, account1 = self.create_account(username="a1", email="a1@a.com")
        _, account2 = self.create_account(username="a2", email="a2@a.com")
        _, account3 = self.create_account(username="a3", email="a3@a.com")
        _, account4 = self.create_account(username="a4", email="a4@a.com")

        # a1 and a2 are in a group
        group, group2 = create_group(slug="my-group-1"), create_group(slug="my-group-2")
        assert group.members.count() == 0
        assert group2.members.count() == 0

        group.add_user(account1)
        group.add_user(account2)

        assert account1.get_friendship_weights() == {
            account1.id: 0.3,  # defined this way
            account2.id: 1.0,  # max
            # account3.id should be missing
        }

        assert account3.get_friendship_weights() == {account3.id: 0.3}

        group2.add_user(account2)
        group2.add_user(account3)
        group2.add_user(account4)

        # account2 is considered better friends with account1 than with
        # account3, because group2 is larger.

        w2_with_1 = account2.get_friendship_weights()[account1.id]
        w2_with_3 = account2.get_friendship_weights()[account3.id]

        assert w2_with_1 > w2_with_3

        # But following has higher weight than groups.

        # Test some methods while we are here:
        assert not account2.is_following(account3)

        account2.follow_user(account3)

        assert account2.is_following(account3)
        assert not account3.is_following(account2)

        # get_friendship_weights is cached, but 'follow_user' clears it, because
        # it's nice for explicit actions to be reflected immediately on the
        # dashboard.

        w2_with_1 = account2.get_friendship_weights()[account1.id]
        w2_with_3 = account2.get_friendship_weights()[account3.id]

        assert w2_with_3 > w2_with_1


class PasswordResetTestsBase:
    def setUp(self):
        super().setUp()
        self.identity, self.account = self.create_account()

    def assertUrlsEqual(self, url, expected):
        """
        Given two URLs, make sure all their components (the ones given by
        urlparse) are equal, only comparing components that are present in both
        URLs.
        """
        fields = ParseResult._fields

        for attr, x, y in zip(fields, urlparse(url), urlparse(expected)):
            if x and y and x != y:
                self.fail(f"{url!r} != {expected!r} ({attr} doesn't match)")

    def test_email_not_found(self):
        # If the provided email is not registered, don't raise any error but
        # also don't send any email.
        self.get_url("login")
        self.fill({"#id_login-email": "not_a_real_email@email.com"})
        self.submit("[name=forgotpassword]")
        assert len(mail.outbox) == 0

    def _test_confirm_start(self):
        self.get_url("login")
        self.fill({"#id_login-email": self.account.email})
        self.submit("[name=forgotpassword]")
        assert len(mail.outbox) == 1
        return self._read_signup_email(mail.outbox[0])

    def _read_signup_email(self, email):
        urlmatch = re.search(r"https?://[^/]*(/.*reset/\S*)", email.body)
        assert urlmatch is not None, "No URL found in sent email"
        return urlmatch.group(), urlmatch.groups()[0]

    def test_confirm_valid(self):
        url, path = self._test_confirm_start()
        self.get_literal_url(path)
        self.assertTextPresent("Please enter your new password")

    def test_confirm_invalid(self):
        url, path = self._test_confirm_start()
        # Let's munge the token in the path, but keep the same length,
        # in case the URLconf will reject a different length.
        path = path[:-5] + ("0" * 4) + path[-1]

        self.get_literal_url(path)
        self.assertTextPresent("The password reset link was invalid")

    def test_confirm_invalid_user(self):
        # Ensure that we get a 200 response for a non-existent user, not a 404
        response = self.client.get("/reset/123456/1-1/")
        self.assertContains(response, "The password reset link was invalid")

    def test_confirm_invalid_post(self):
        # Same as test_confirm_invalid, but trying
        # to do a POST instead.
        url, path = self._test_confirm_start()
        path = path[:-5] + ("0" * 4) + path[-1]

        self.client.post(
            path,
            {
                "new_password1": "anewpassword",
                "new_password2": "anewpassword",
            },
        )
        # Check the password has not been changed
        account = Account.objects.get(id=self.account.id)
        assert not account.check_password("anewpassword")

    def test_confirm_complete(self):
        url, path = self._test_confirm_start()
        self.get_literal_url(path)
        self.fill({"#id_new_password1": "anewpassword", "#id_new_password2": "anewpassword"})
        self.submit(".maincontent [type=submit]")
        # Check the password has been changed
        account = Account.objects.get(id=self.account.id)
        assert account.check_password("anewpassword")

        # Check we can't use the link again
        self.get_literal_url(path)
        self.assertTextPresent("The password reset link was invalid")

    def test_confirm_different_passwords(self):
        url, path = self._test_confirm_start()
        self.get_literal_url(path)
        self.fill({"#id_new_password1": "anewpassword", "#id_new_password2": "x"})
        self.submit(".maincontent [type=submit]")
        self.assertTextPresent(AccountSetPasswordForm.error_messages["password_mismatch"])


class PasswordResetTestsWT(PasswordResetTestsBase, WebTestBase):
    pass


class PasswordResetTestsFB(PasswordResetTestsBase, FullBrowserTest):
    pass


class PasswordChangeTestsBase:
    def setUp(self):
        super().setUp()
        self.identity, self.account = self.create_account()

    def test_change_valid(self):
        self.login(self.account, shortcut=False)
        self.get_url("learnscripture_password_change")
        self.fill(
            {
                "#id_old_password": "password",
                "#id_new_password1": "newpassword",
                "#id_new_password2": "newpassword",
            }
        )
        self.submit('.maincontent [type="submit"]')
        self.assertTextPresent("Your password was changed.")

        # Should be logged in:
        # - name should appear on page
        self.assertTextPresent(self.account.username)

        # - should not be redirected to login
        self.get_url("learnscripture_password_change")
        self.assertUrlsEqual(reverse("learnscripture_password_change"))

        # password should actually be changed.
        account = Account.objects.get(id=self.account.id)
        assert account.check_password("newpassword")


class PasswordChangeTestsWT(PasswordChangeTestsBase, WebTestBase):
    pass


class PasswordChangeTestsFB(PasswordChangeTestsBase, FullBrowserTest):
    pass
