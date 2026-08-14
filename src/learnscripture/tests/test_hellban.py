from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone
from django_functest import FuncBaseMixin
from time_machine import travel

from moderation import models as moderation
from moderation.models import ModerationActionType

from .base import BibleVersesMixin, FullBrowserTest, TestBase, WebTestBase, create_account

# hellbanning affects lots of things, and tests are in other places.
# Tests here are for the moderator-visible hellban function


class HellbanPageTestsBase(FuncBaseMixin):
    def test_hellban(self):
        _, account = create_account(username="baduser")
        _, moderator = create_account(is_moderator=True)

        self.login(moderator)
        self.get_url("user_stats", account.username)
        self.submit("[name=hellban-48hours]", wait_for_reload=False)
        account.refresh_from_db()

        assert account.is_hellbanned
        assert account.moderation_actions.get().duration == timedelta(days=2)

        # Check we can unhellban

        self.submit("[name=unhellban]", wait_for_reload=False)
        account.refresh_from_db()
        assert not account.is_hellbanned


class HellbanPageTestsFB(HellbanPageTestsBase, FullBrowserTest):
    pass


class HellbanPageTestsWT(HellbanPageTestsBase, WebTestBase):
    pass


class HellbanTests(BibleVersesMixin, TestBase):
    def test_hellban_reversing(self):
        _, account = create_account(username="baduser")
        _, moderator = create_account(is_moderator=True)

        moderation.hellban_user(account, by=moderator, duration=timedelta(days=2))
        account.refresh_from_db()

        assert account.is_hellbanned
        assert account.moderation_actions.get().duration == timedelta(days=2)

        with travel(timezone.now()) as tm:
            tm.shift(timedelta(days=1))
            call_command("run_moderation_adjustments")
            account.refresh_from_db()
            # Should not be reversed yet
            assert account.is_hellbanned

            tm.shift(timedelta(days=1.1))
            call_command("run_moderation_adjustments")
            account.refresh_from_db()
            assert not account.is_hellbanned
            assert account.moderation_actions.get().reversed_at is not None

    def test_hellban_cycle(self):
        _, account = create_account(username="baduser")
        _, moderator = create_account(is_moderator=True)

        moderation.hellban_user(account, by=moderator, duration=timedelta(days=2))
        account.refresh_from_db()
        assert account.is_hellbanned

        assert (
            account.moderation_actions.filter(action_type=ModerationActionType.USER_HELLBANNED).reversible().count()
            == 1
        )

        moderation.unhellban_user(account, by=moderator)
        account.refresh_from_db()
        assert not account.is_hellbanned

        # If we re-ban, we shouldn't have multiple records that are waiting
        # to be reversed:

        moderation.hellban_user(account, by=moderator, duration=timedelta(days=2))
        account.refresh_from_db()
        assert account.is_hellbanned

        assert (
            account.moderation_actions.filter(action_type=ModerationActionType.USER_HELLBANNED).reversible().count()
            == 1
        )
