from __future__ import absolute_import

from django.core.urlresolvers import reverse
from django.test import TestCase

from accounts.models import Account, Identity
from awards.models import Award, AwardType
from groups.models import Group
from events.models import Event, EventType

from .base import LiveServerTests


class GroupPageTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def test_join(self):
        identity, account = self.create_account()
        self.login(account)

        creator_account = Account.objects.get(username='account')

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
        driver.get(self.live_server_url + reverse('groups'))

        self.assertIn("Another group", driver.page_source)
        self.assertNotIn("My group", driver.page_source)
        driver.find_element_by_xpath('//a[text() = "See more"]').click()

        self.assertTrue(driver.current_url.endswith('/groups/another-group/'))

        driver.find_element_by_css_selector('input[name="join"]').click()
        self.wait_until_loaded('body')
        self.assertTrue(public_group.members.filter(id=account.id).exists())

        self.assertEqual(Event.objects.filter(event_type=EventType.GROUP_JOINED).count(),
                         1)

    def test_join_from_no_account(self):
        creator_account = Account.objects.get(username='account')
        g = Group.objects.create(name='My group',
                                 slug='my-group',
                                 created_by=creator_account,
                                 public=True,
                                 open=True)
        driver = self.driver
        driver.get(self.live_server_url + reverse('group', args=(g.slug,)))

        self.assertIn("You are not a member of this group", driver.page_source)

        driver.find_element_by_css_selector('input[name="join"]').click()

        self.fill_in_account_form()
        self.wait_until_loaded('body')

        self.assertIn("You are a member of this group", driver.page_source)


class GroupTests(TestCase):

    def test_organizer_award(self):
        creator_account = Account.objects.create(username='creator',
                                                 email='c@example.com')
        Identity.objects.create(account=creator_account)
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


class GroupCreatePageTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def test_create(self):
        identity, account = self.create_account()
        self.login(account)

        invited_account = Account.objects.create(username='invitee',
                                                 email='i@example.com')
        Identity.objects.create(account=invited_account)

        driver = self.driver
        driver.get(self.live_server_url + reverse('create_group'))
        driver.find_element_by_id('id_name').send_keys('My group')
        driver.find_element_by_id('id_public').click()

        driver.find_element_by_id('id_invited_users_0').send_keys('invit')
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
