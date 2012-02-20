from __future__ import absolute_import
import time, re

from django.core.urlresolvers import reverse
from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.support.ui import Select

from bibleverses.models import VerseSet

from .base import LiveServerTests


class ViewSetTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def setUp(self):
        super(ViewSetTests, self).setUp()
        self._identity, self._account = self.create_account()

    def test_change_version(self):
        driver = self.driver
        self.login(self._account)
        vs = VerseSet.objects.get(slug='bible-101')
        driver.get(self.live_server_url + reverse('view_verse_set', kwargs=dict(slug=vs.slug)))

        self.assertIn("saith", driver.page_source)

        Select(driver.find_element_by_id("id-version-select")).select_by_visible_text("NET")

        self.wait_until_loaded('body')
        self.assertIn("replied", driver.page_source)
