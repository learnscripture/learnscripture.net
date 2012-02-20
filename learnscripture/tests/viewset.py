from __future__ import absolute_import
import time, re

from django.core.urlresolvers import reverse
from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.support.ui import Select

from accounts.models import Identity
from bibleverses.models import VerseSet

from .base import LiveServerTests


class ViewSetTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def setUp(self):
        super(ViewSetTests, self).setUp()

    def test_change_version(self):
        driver = self.driver
        identity, account = self.create_account()
        self.login(account)
        vs = VerseSet.objects.get(slug='bible-101')
        driver.get(self.live_server_url + reverse('view_verse_set', kwargs=dict(slug=vs.slug)))

        self.assertIn("saith", driver.page_source)

        Select(driver.find_element_by_id("id-version-select")).select_by_visible_text("NET")

        self.wait_until_loaded('body')
        self.assertIn("replied", driver.page_source)

    def test_learn_selected_version(self):
        driver = self.driver
        identity, account = self.create_account()
        self.login(account)
        vs = VerseSet.objects.get(slug='bible-101')

        self.assertEqual(identity.verse_statuses.all().count(), 0)

        driver.get(self.live_server_url + reverse('view_verse_set', kwargs=dict(slug=vs.slug))
                   + "?version=NET")
        driver.find_element_by_css_selector("input[value='Learn']").click()

        # Can use 'all' here because this is the first time we've chosen anything
        verse_statuses = identity.verse_statuses.all()
        self.assertTrue(len(verse_statuses) > 0)
        self.assertTrue(all(uvs.version.slug == 'NET' for uvs in verse_statuses))

    def test_view_without_identity(self):
        driver = self.driver
        vs = VerseSet.objects.get(slug='bible-101')
        self.assertEqual(Identity.objects.all().count(), 0)
        driver.get(self.live_server_url + reverse('view_verse_set', kwargs=dict(slug=vs.slug)))
        self.wait_until_loaded('body')
        # Default version is NET:
        self.assertIn("Jesus replied", driver.page_source)

        # Shouldn't have created an Identity

        self.assertEqual(Identity.objects.all().count(), 0)
