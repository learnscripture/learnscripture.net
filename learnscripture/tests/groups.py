from __future__ import absolute_import

from django.core.urlresolvers import reverse
from django.test import TestCase

from accounts.models import Account, Identity
from awards.models import Award, AwardType
from groups.models import Group
from events.models import Event, EventType

from .base import LiveServerTests, AccountTestMixin


class GroupPageTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

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


        driver = self.driver
        self.get_url('groups')

        self.assertIn("Another group", driver.page_source)
        self.assertNotIn("My group", driver.page_source)
        driver.find_element_by_xpath('//a[text() = "Another group"]').click()

        self.assertTrue(driver.current_url.endswith('/groups/another-group/'))

        driver.find_element_by_css_selector('input[name="join"]').click()
        self.wait_until_loaded('body')
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
        driver = self.driver
        self.get_url('group', args=(g.slug,))

        self.assertIn("You are not a member of this group", driver.page_source)

        driver.find_element_by_css_selector('input[name="join"]').click()

        self.wait_until_loaded('body')
        self.fill_in_account_form()
        self.wait_until_loaded('body')
        driver.find_element_by_css_selector('input[name="join"]').click()
        self.wait_until_loaded('body')

        self.assertIn("You are a member of this group", driver.page_source)


class GroupTests(AccountTestMixin, TestCase):

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
        i, creator_account = self.create_account(username='creator',
                                                 email='c@example.com')
        group = Group.objects.create(name='My group',
                                     slug='my-group',
                                     created_by=creator_account,
                                     public=True,
                                     open=True)

        i, member1 = self.create_account(username='member1',
                                         email='m1@example.com')
        i, member2 = self.create_account(username='member2',
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


class GroupCreatePageTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def test_create(self):
        identity, account = self.create_account()
        self.login(account)

        _, invited_account = self.create_account(username='invitee',
                                              email='i@example.com')

        driver = self.driver
        self.get_url('create_group')
        driver.find_element_by_css_selector("#id_name").send_keys("My group")
        driver.find_element_by_css_selector("#id_public").click()

        driver.find_element_by_css_selector("#id_invited_users_0").send_keys("invit")
        self.wait_for_ajax()
        driver.find_element_by_css_selector('ul.ui-autocomplete li.ui-menu-item:first-child').click()
        driver.find_element_by_css_selector('input[name="save"]').click()
        self.wait_until_loaded('body')

        self.assertTrue(driver.current_url.endswith('/my-group/'))

        g = Group.objects.get(slug='my-group')
        self.assertEqual(list(g.invited_users()), [invited_account])

        self.assertIn('invited you to join', invited_account.identity.notices.all()[0].message_html)

        self.assertEqual(Event.objects.filter(event_type=EventType.GROUP_CREATED).count(),
                         1)
