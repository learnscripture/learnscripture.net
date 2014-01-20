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

    def test_change_version(self):
        driver = self.driver
        identity, account = self.create_account()
        self.login(account)
        vs = VerseSet.objects.get(slug='bible-101')
        self.get_url('view_verse_set', kwargs=dict(slug=vs.slug))

        self.assertIn("saith", driver.page_source)

        Select(self.find("#id-version-select")).select_by_visible_text("NET (New English Translation)")

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
        self.click("input[value='Learn']")

        # Can use 'all' here because this is the first time we've chosen anything
        verse_statuses = identity.verse_statuses.all()
        self.assertTrue(len(verse_statuses) > 0)
        self.assertTrue(all(uvs.version.slug == 'NET' for uvs in verse_statuses))

    def test_drop_from_queue(self):
        driver = self.driver
        identity, account = self.create_account()
        self.login(account)
        vs = VerseSet.objects.get(slug='bible-101')
        identity.add_verse_set(vs)
        self.assertEqual(len(identity.bible_verse_statuses_for_learning(vs.id)),
                         vs.verse_choices.count())

        self.get_url('view_verse_set', kwargs=dict(slug=vs.slug))

        self.assertIn("You have %d verse(s) from this set in your queue" % vs.verse_choices.count(),
                      driver.page_source)

        self.click("input[name='drop']")

        self.assertEqual(len(identity.bible_verse_statuses_for_learning(vs.id)),
                         0)

    def test_view_without_identity(self):
        ids = list(Identity.objects.all())

        driver = self.driver
        vs = VerseSet.objects.get(slug='bible-101')
        self.assertEqual(Identity.objects.exclude(id__in=[i.id for i in ids]).all().count(), 0)
        self.get_url('view_verse_set', kwargs=dict(slug=vs.slug))
        # Default version is NET:
        self.assertIn("Jesus replied", driver.page_source)

        # Shouldn't have created an Identity

        self.assertEqual(Identity.objects.exclude(id__in=[i.id for i in ids]).all().count(), 0)
