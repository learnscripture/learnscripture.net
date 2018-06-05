import time

from django.urls import reverse

from accounts.models import Account
from awards.models import Award, AwardType
from comments.models import Comment
from events.models import Event, EventType, GroupJoinedEvent
from groups.models import Group

from .base import AccountTestMixin, FullBrowserTest, TestBase, WebTestBase, get_or_create_any_account
from .test_bibleverses import RequireExampleVerseSetsMixin


def create_group(**fields):
    defaults = dict(
        slug='my-group'
    )
    defaults.update(fields)
    if 'created_by' not in fields:
        defaults['created_by'] = get_or_create_any_account()
    return Group.objects.create(**defaults)


class GroupPageTestsBase(RequireExampleVerseSetsMixin):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def test_join(self):
        identity, account = self.create_account()
        self.login(account)

        _, creator_account = self.create_account(username='creator',
                                                 email='c@example.com')

        private_group = Group.objects.create(name='My group',
                                             slug='my-group',
                                             created_by=creator_account,
                                             public=False,
                                             open=False)
        public_group = Group.objects.create(name='Another group',
                                            slug='another-group',
                                            created_by=creator_account,
                                            public=True,
                                            open=True)

        self.assertEqual(private_group.can_join(account), False)
        self.assertEqual(public_group.can_join(account), True)
        self.get_url('groups')
        self.fill({'#id-search-input': 'group'})
        self.submit('#id-search-btn')

        self.assertTextPresent("Another group")
        self.assertTextAbsent("My group")
        self.follow_link('a[href="{0}"]'.format(reverse('group', args=('another-group',))))

        self.assertUrlsEqual(reverse('group', args=('another-group',)))

        self.submit('input[name="join"]')
        self.assertTrue(public_group.members.filter(id=account.id).exists())

        self.assertEqual(Event.objects.filter(event_type=EventType.GROUP_JOINED).count(),
                         1)

    def test_join_from_no_account(self):
        _, creator_account = self.create_account(username='creator',
                                                 email='c@example.com')

        g = Group.objects.create(name='My group',
                                 slug='my-group',
                                 created_by=creator_account,
                                 public=True,
                                 open=True)
        self.get_url('group', g.slug)

        self.assertTextPresent("You are not a member of this group")

        self.submit('input[name="join"]')

        self.fill_in_account_form()
        self.submit('input[name="join"]')

        self.assertTextPresent("You are a member of this group")


class GroupPageTestsFB(GroupPageTestsBase, FullBrowserTest):

    # Additional Selenium only test

    def test_add_comment(self):
        _, creator_account = self.create_account(username='creator',
                                                 email='c@example.com')

        g = Group.objects.create(name='My group',
                                 slug='my-group',
                                 created_by=creator_account,
                                 public=True,
                                 open=True)
        self.login(creator_account)
        self.get_url('group', g.slug)
        self.click('.show-add-comment')
        message = "Yay this is my comment!"
        self.fill({'#id-comment-box': message})
        self.click('#id-add-comment-btn')
        self.wait_for_ajax()
        self.assertTextPresent(message)
        # Test db
        c = Comment.objects.get()
        self.assertEqual(c.author, creator_account)
        self.assertEqual(c.message, "Yay this is my comment!")


class GroupPageTestsWT(GroupPageTestsBase, WebTestBase):
    pass


class GroupTests(AccountTestMixin, TestBase):

    def test_organizer_award(self):
        i, creator_account = self.create_account(username='creator',
                                                 email='c@example.com')
        g = Group.objects.create(name='My group',
                                 slug='my-group',
                                 created_by=creator_account,
                                 public=True,
                                 open=True)
        g.add_user(creator_account)

        for i in range(1, 7):
            account = Account.objects.create(username='joiner%d' % i,
                                             email='j%d@example.com' % i)
            g.add_user(account)
            self.assertEqual(Award.objects.filter(account=creator_account,
                                                  award_type=AwardType.ORGANIZER).count(),
                             0 if i < 5 else 1)

    def test_visibility(self):
        i, creator_account = self.create_account(username='creator',
                                                 email='c@example.com')
        group = Group.objects.create(name='My group',
                                     slug='my-group',
                                     created_by=creator_account,
                                     public=True,
                                     open=True)
        group.add_user(creator_account)

        i, viewer_account = self.create_account(username='viewer',
                                                email='v@example.com')

        visible = lambda: Group.objects.visible_for_account(viewer_account)

        self.assertEqual([g.name for g in visible()],
                         ["My group"])

        # Private groups should not be visible
        group.public = False
        group.save()
        self.assertEqual(list(visible()),
                         [])

        # But should be visible if invited
        group.set_invitation_list([viewer_account])
        self.assertEqual([g.name for g in visible()],
                         ["My group"])

        # (Reset)
        group.invitations.all().delete()
        self.assertEqual(list(visible()),
                         [])

        # or if a member
        group.add_user(viewer_account)
        self.assertEqual([g.name for g in visible()],
                         ["My group"])

        # Reset
        group.public = True
        group.remove_user(viewer_account)
        group.save()

        # Shouldn't be visible if creator is hellbanned
        creator_account.is_hellbanned = True
        creator_account.save()
        group.invitations.all().delete()
        self.assertEqual(list(visible()),
                         [])

    def test_set_invitation_list(self):
        _, creator_account = self.create_account(username='creator',
                                                 email='c@example.com')
        group = Group.objects.create(name='My group',
                                     slug='my-group',
                                     created_by=creator_account,
                                     public=True,
                                     open=True)

        _, member1 = self.create_account(username='member1',
                                         email='m1@example.com')
        _, member2 = self.create_account(username='member2',
                                         email='m2@example.com')

        group.set_invitation_list([member1])

        self.assertEqual([i.account.username for i in group.invitations.all()],
                         ["member1"])

        self.assertEqual([i.group.name for i in member1.invitations.all()],
                         ["My group"])

        group.set_invitation_list([member2])

        self.assertEqual([i.account.username for i in group.invitations.all()],
                         ["member2"])

        self.assertEqual([i.group.name for i in member1.invitations.all()],
                         [])

        self.assertEqual([i.group.name for i in member2.invitations.all()],
                         ["My group"])

        # hellbanned users are ignored when they invite others:
        creator_account.is_hellbanned = True
        creator_account.save()
        group = Group.objects.get(id=group.id)
        group.set_invitation_list([member1])

        self.assertEqual([i.group.name for i in member1.invitations.all()],
                         [])

    def test_add_comment(self):
        i, creator_account = self.create_account(username='creator',
                                                 email='c@example.com')
        group = Group.objects.create(name='My group',
                                     slug='my-group',
                                     created_by=creator_account,
                                     public=True,
                                     open=True)

        i, other_account = self.create_account(username='a',
                                               email='a@example.com')

        self.assertTrue(group.accepts_comments_from(other_account))

        group.public = False
        group.save()

        self.assertFalse(group.accepts_comments_from(other_account))

        group.add_user(other_account)

        self.assertTrue(group.accepts_comments_from(other_account))

        group.add_comment(author=other_account,
                          message="Hello")

        self.assertEqual(["Hello"],
                         [c.message for c in group.comments.all()])


class GroupCreatePageTests(RequireExampleVerseSetsMixin, FullBrowserTest):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def test_create(self):
        identity, account = self.create_account()
        self.login(account)

        _, invited_account = self.create_account(username='invitee',
                                                 email='i@example.com')

        self.get_url('create_group')
        self.fill({"#id_name": "My group"})
        self.click("#id_public")

        select_input = "input.select2-search__field"
        self.click(select_input)
        self.fill({select_input: "invit"})
        self.wait_for_ajax()
        time.sleep(0.2)
        self.press_enter(select_input)
        time.sleep(0.2)
        self.click('input[name="save"]')

        self.assertUrlsEqual(reverse('group', args=('my-group',)))

        g = Group.objects.get(slug='my-group')
        self.assertEqual(list(g.invited_users()), [invited_account])
        self.assertIn('invited you to join', invited_account.identity.notices.all()[0].message_html)

        self.assertEqual(Event.objects.filter(event_type=EventType.GROUP_CREATED).count(),
                         1)


# Use Django client
class GroupPageTests2(AccountTestMixin, TestBase):
    def test_comments_on_related_events(self):
        _, account = self.create_account()
        group = create_group(public=True)
        event = GroupJoinedEvent(account=account,
                                 group=group).save()
        comment = Comment.objects.create(group=group,
                                         event=event,
                                         author=account,
                                         message="Hello there!")
        response = self.client.get(reverse('group', args=(group.slug,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello there!")
        self.assertContains(response, comment.get_absolute_url())
