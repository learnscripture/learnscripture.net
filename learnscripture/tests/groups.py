from __future__ import absolute_import

from django.core.urlresolvers import reverse

from accounts.models import Account
from groups.models import Group
from events.models import Event, EventType

from .base import LiveServerTests


class GroupPageTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def setUp(self):
        super(GroupPageTests, self).setUp()

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
