from __future__ import absolute_import

from datetime import timedelta
from decimal import Decimal
import itertools
import re

from autofixture import AutoFixture
from django.core import mail
from django.db.models import F
from django.test import TestCase
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.six.moves.urllib.parse import urlparse, ParseResult

from accounts.models import Account, ActionChange, Identity
from awards.models import AwardType, Award
from bibleverses.models import MemoryStage, StageType
from events.models import Event, EventType
from groups.models import Group
from learnscripture.forms import AccountSetPasswordForm
from scores.models import Scores, ScoreReason

from .base import AccountTestMixin

__all__ = ['AccountTests', 'PasswordResetTest']

class AccountTests(AccountTestMixin, TestCase):
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
        _, a = self.create_account()
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
        _, account = self.create_account()

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
        _, a = self.create_account()

        a.award_action_points("John 3:16", "This is John 3:16",
                              MemoryStage.TESTED,
                              ActionChange(old_strength=0.7, new_strength=0.99),
                              StageType.TEST, 0.9)
        self.assertEqual(a.total_score.points,
                         (4 * Scores.POINTS_PER_WORD * 0.9)
                         + (4 * Scores.POINTS_PER_WORD * Scores.VERSE_LEARNT_BONUS))


    def test_addict_award(self):
        import awards.tasks
        _, account = self.create_account()

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

    def test_friendship_weights(self):
        _, account1 = self.create_account(username="a1",
                                          email="a1@a.com")
        _, account2 = self.create_account(username="a2",
                                          email="a2@a.com")
        _, account3 = self.create_account(username="a3",
                                          email="a3@a.com")
        _, account4 = self.create_account(username="a4",
                                          email="a4@a.com")

        # a1 and a2 are in a group
        group, group2 = AutoFixture(Group).create(2)
        assert group.members.count() == 0
        assert group2.members.count() == 0

        group.add_user(account1)
        group.add_user(account2)

        self.assertEqual(account1.get_friendship_weights(),
                         {account1.id: 0.3,  # defined this way
                          account2.id: 1.0,  # max
                          # account3.id should be missing
                          })


        self.assertEqual(account3.get_friendship_weights(),
                         {account3.id: 0.3})

        group2.add_user(account2)
        group2.add_user(account3)
        group2.add_user(account4)

        # account2 is considered better friends with account1 than with
        # account3, because group2 is larger.

        w2_with_1 = account2.get_friendship_weights()[account1.id]
        w2_with_3 = account2.get_friendship_weights()[account3.id]

        self.assertTrue(w2_with_1 > w2_with_3)

        # But following has higher weight than groups.

        # Test some methods while we are here:
        self.assertFalse(account2.is_following(account3))

        account2.follow_user(account3)

        self.assertTrue(account2.is_following(account3))
        self.assertFalse(account3.is_following(account2))

        # get_friendship_weights is cached, but 'follow_user' clears it, because
        # it's nice for explicit actions to be reflected immediately on the
        # dashboard.

        w2_with_1 = account2.get_friendship_weights()[account1.id]
        w2_with_3 = account2.get_friendship_weights()[account3.id]

        self.assertTrue(w2_with_3 > w2_with_1)


class PasswordResetTest(TestCase):

    def setUp(self):
        super(PasswordResetTest, self).setUp()
        account = Account.objects.create(username='any_user',
                                         email='any_user@example.com')
        account.set_password('foo')
        account.save()

    def assertURLEqual(self, url, expected, parse_qs=False):
        """
        Given two URLs, make sure all their components (the ones given by
        urlparse) are equal, only comparing components that are present in both
        URLs.
        If `parse_qs` is True, then the querystrings are parsed with QueryDict.
        This is useful if you don't want the order of parameters to matter.
        Otherwise, the query strings are compared as-is.
        """
        fields = ParseResult._fields

        for attr, x, y in zip(fields, urlparse(url), urlparse(expected)):
            if parse_qs and attr == 'query':
                x, y = QueryDict(x), QueryDict(y)
            if x and y and x != y:
                self.fail("%r != %r (%s doesn't match)" % (url, expected, attr))

    def assertFormError(self, response, error):
        """Assert that error is found in response.context['form'] errors"""
        form_errors = list(itertools.chain(*response.context['form'].errors.values()))
        self.assertIn(force_text(error), form_errors)

    def test_email_not_found(self):
        """If the provided email is not registered, don't raise any error but
        also don't send any email."""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/login/', {'login-email': 'not_a_real_email@email.com',
                                                'forgotpassword': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def _test_confirm_start(self):
        # Start by creating the email
        response = self.client.post('/login/', {'login-email': 'any_user@example.com',
                                                'forgotpassword': '1'})
        self.assertURLEqual(response.url, '/password-reset/')
        self.assertEqual(len(mail.outbox), 1)
        return self._read_signup_email(mail.outbox[0])

    def _read_signup_email(self, email):
        urlmatch = re.search(r"https?://[^/]*(/.*reset/\S*)", email.body)
        self.assertTrue(urlmatch is not None, "No URL found in sent email")
        return urlmatch.group(), urlmatch.groups()[0]

    def test_confirm_valid(self):
        url, path = self._test_confirm_start()
        response = self.client.get(path)
        # redirect to a 'complete' page:
        self.assertContains(response, "Please enter your new password")

    def test_confirm_invalid(self):
        url, path = self._test_confirm_start()
        # Let's munge the token in the path, but keep the same length,
        # in case the URLconf will reject a different length.
        path = path[:-5] + ("0" * 4) + path[-1]

        response = self.client.get(path)
        self.assertContains(response, "The password reset link was invalid")

    def test_confirm_invalid_user(self):
        # Ensure that we get a 200 response for a non-existant user, not a 404
        response = self.client.get('/reset/123456/1-1/')
        self.assertContains(response, "The password reset link was invalid")

    def test_confirm_invalid_post(self):
        # Same as test_confirm_invalid, but trying
        # to do a POST instead.
        url, path = self._test_confirm_start()
        path = path[:-5] + ("0" * 4) + path[-1]

        self.client.post(path, {
            'new_password1': 'anewpassword',
            'new_password2': 'anewpassword',
        })
        # Check the password has not been changed
        u = Account.objects.get(email='any_user@example.com')
        self.assertTrue(not u.check_password("anewpassword"))

    def test_confirm_complete(self):
        url, path = self._test_confirm_start()
        response = self.client.post(path, {'new_password1': 'anewpassword',
                                           'new_password2': 'anewpassword'})
        # Check the password has been changed
        u = Account.objects.get(email='any_user@example.com')
        self.assertTrue(u.check_password("anewpassword"))

        # Check we can't use the link again
        response = self.client.get(path)
        self.assertContains(response, "The password reset link was invalid")

    def test_confirm_different_passwords(self):
        url, path = self._test_confirm_start()
        response = self.client.post(path, {'new_password1': 'anewpassword',
                                           'new_password2': 'x'})
        self.assertFormError(response, AccountSetPasswordForm.error_messages['password_mismatch'])

