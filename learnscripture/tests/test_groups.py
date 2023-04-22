import time

from django.urls import reverse

from accounts.models import Account
from awards.models import Award, AwardType
from comments.models import Comment
from events.models import Event, EventType, GroupJoinedEvent
from groups.models import Group

from .base import AccountTestMixin, FullBrowserTest, TestBase, WebTestBase, create_account, get_or_create_any_account
from .test_bibleverses import RequireExampleVerseSetsMixin


def create_group(*, slug="my-group", created_by=None, public=False, quietened=False) -> Group:
    if created_by is None:
        created_by = get_or_create_any_account()
    return Group.objects.create(
        slug=slug,
        created_by=created_by,
        public=public,
        quietened=quietened,
    )


class GroupPageTestsBase(RequireExampleVerseSetsMixin):
    def test_join(self):
        identity, account = self.create_account()
        self.login(account)

        _, creator_account = self.create_account(username="creator", email="c@example.com")

        private_group = Group.objects.create(
            name="My group", slug="my-group", created_by=creator_account, public=False, open=False
        )
        public_group = Group.objects.create(
            name="Another group", slug="another-group", created_by=creator_account, public=True, open=True
        )

        assert not private_group.can_join(account)
        assert public_group.can_join(account)
        self.get_url("groups")
        self.fill({"#id_query": "group"})
        if self.is_full_browser_test:
            self.click("#id-search-btn")
        else:
            self.submit("#id-search-btn")

        self.assertTextPresent("Another group")
        self.assertTextAbsent("My group")
        self.follow_link(f"a[href=\"{reverse('group', args=('another-group',))}\"]")

        self.assertUrlsEqual(reverse("group", args=("another-group",)))

        self.submit('[name="join"]', wait_for_reload=False)
        assert public_group.members.filter(id=account.id).exists()

        assert Event.objects.filter(event_type=EventType.GROUP_JOINED).count() == 1

    def test_join_from_no_account(self):
        _, creator_account = self.create_account(username="creator", email="c@example.com")

        g = Group.objects.create(name="My group", slug="my-group", created_by=creator_account, public=True, open=True)
        self.get_url("group", g.slug)

        self.assertTextPresent("You are not a member of this group")

        self.submit('[name="join"]')

        self.fill_in_account_form()
        self.submit('[name="join"]', wait_for_reload=False)

        self.assertTextPresent("You are a member of this group")

    def test_quieten(self):
        group = create_group(public=True, quietened=False)
        _, moderator = create_account(is_moderator=True)
        self.login(moderator)
        self.get_url("group", group.slug)
        self.submit("[name=quieten]", wait_for_reload=False)
        group.refresh_from_db()
        assert group.quietened
        assert group.moderation_actions.exists()
        assert group.moderation_actions.get().action_by == moderator

        self.submit("[name=unquieten]", wait_for_reload=False)
        group.refresh_from_db()
        assert not group.quietened


class GroupPageTestsFB(GroupPageTestsBase, FullBrowserTest):

    # Additional Selenium only test

    def test_add_comment(self):
        _, creator_account = self.create_account(username="creator", email="c@example.com")

        g = Group.objects.create(name="My group", slug="my-group", created_by=creator_account, public=True, open=True)
        self.login(creator_account)
        self.get_url("group", g.slug)
        self.click(".show-add-comment")
        message = "Yay this is my comment!"
        self.fill({".commentblock .comment-box": message})
        self.click(".commentblock .add-comment-btn")
        self.wait_for_ajax()
        self.assertTextPresent(message)
        # Test db
        c = Comment.objects.get()
        assert c.author == creator_account
        assert c.message == "Yay this is my comment!"


class GroupPageTestsWT(GroupPageTestsBase, WebTestBase):
    pass


class GroupTests(AccountTestMixin, TestBase):
    def test_organizer_award(self):
        i, creator_account = self.create_account(username="creator", email="c@example.com")
        g = Group.objects.create(name="My group", slug="my-group", created_by=creator_account, public=True, open=True)
        g.add_user(creator_account)

        for i in range(1, 7):
            account = Account.objects.create(username="joiner%d" % i, email="j%d@example.com" % i)
            g.add_user(account)
            assert Award.objects.filter(account=creator_account, award_type=AwardType.ORGANIZER).count() == (
                0 if i < 5 else 1
            )

    def test_visibility(self):
        i, creator_account = self.create_account(username="creator", email="c@example.com")
        group = Group.objects.create(
            name="My group", slug="my-group", created_by=creator_account, public=True, open=True
        )
        group.add_user(creator_account)

        i, viewer_account = self.create_account(username="viewer", email="v@example.com")

        visible = lambda: Group.objects.visible_for_account(viewer_account)

        assert [g.name for g in visible()] == ["My group"]

        # Private groups should not be visible
        group.public = False
        group.save()
        assert list(visible()) == []

        # But should be visible if invited
        group.set_invitation_list([viewer_account])
        assert [g.name for g in visible()] == ["My group"]

        # (Reset)
        group.invitations.all().delete()
        assert list(visible()) == []

        # or if a member
        group.add_user(viewer_account)
        assert [g.name for g in visible()] == ["My group"]

        # Reset
        group.public = True
        group.remove_user(viewer_account)
        group.save()

        # Shouldn't be visible if creator is hellbanned
        creator_account.is_hellbanned = True
        creator_account.save()
        group.invitations.all().delete()
        assert list(visible()) == []

    def test_set_invitation_list(self):
        _, creator_account = self.create_account(username="creator", email="c@example.com")
        group = Group.objects.create(
            name="My group", slug="my-group", created_by=creator_account, public=True, open=True
        )

        _, member1 = self.create_account(username="member1", email="m1@example.com")
        _, member2 = self.create_account(username="member2", email="m2@example.com")

        group.set_invitation_list([member1])

        assert [i.account.username for i in group.invitations.all()] == ["member1"]

        assert [i.group.name for i in member1.invitations.all()] == ["My group"]

        group.set_invitation_list([member2])

        assert [i.account.username for i in group.invitations.all()] == ["member2"]

        assert [i.group.name for i in member1.invitations.all()] == []

        assert [i.group.name for i in member2.invitations.all()] == ["My group"]

        assert [m.message_html for m in member1.identity.notices.all()] == [
            '<a href="/user/creator/">creator</a> invited you to join the group '
            '<a href="/groups/my-group/">My group</a>'
        ]

        # hellbanned users are ignored when they invite others:
        creator_account.is_hellbanned = True
        creator_account.save()
        group = Group.objects.get(id=group.id)
        group.set_invitation_list([member1])

        assert [i.group.name for i in member1.invitations.all()] == []

    def test_add_comment(self):
        i, creator_account = self.create_account(username="creator", email="c@example.com")
        group = Group.objects.create(
            name="My group", slug="my-group", created_by=creator_account, public=True, open=True
        )

        i, other_account = self.create_account(username="a", email="a@example.com")

        assert group.accepts_comments_from(other_account)

        group.public = False
        group.save()

        assert not group.accepts_comments_from(other_account)

        group.add_user(other_account)

        assert group.accepts_comments_from(other_account)

        group.add_comment(author=other_account, message="Hello")

        assert ["Hello"] == [c.message for c in group.comments.all()]


class GroupCreatePageTests(RequireExampleVerseSetsMixin, FullBrowserTest):
    def test_create(self):
        identity, account = self.create_account()
        self.login(account)

        _, invited_account = self.create_account(username="invitee", email="i@example.com")

        self.get_url("create_group")
        self.fill({"#id_name": "My group"})
        self.click("#id_public")

        select_input = "input.select2-search__field"
        self.click(select_input)
        self.fill({select_input: "invit"})
        self.wait_for_ajax()
        self.wait_until_loaded(".select2-results__option--highlighted")
        self.press_enter(select_input)
        time.sleep(0.2)
        self.submit('[name="save"]')

        self.assertUrlsEqual(reverse("group", args=("my-group",)))

        g = Group.objects.get(slug="my-group")
        assert list(g.invited_users()) == [invited_account]
        assert "invited you to join" in invited_account.identity.notices.all()[0].message_html

        assert Event.objects.filter(event_type=EventType.GROUP_CREATED).count() == 1


# Use Django client
class GroupPageTests2(AccountTestMixin, TestBase):
    def test_comments_on_related_events(self):
        _, account = self.create_account()
        group = create_group(public=True)
        event = GroupJoinedEvent(account=account, group=group).save()
        comment = Comment.objects.create(group=group, event=event, author=account, message="Hello there!")
        response = self.client.get(reverse("group", args=(group.slug,)))
        assert response.status_code == 200
        self.assertContains(response, "Hello there!")
        self.assertContains(response, comment.get_absolute_url())
