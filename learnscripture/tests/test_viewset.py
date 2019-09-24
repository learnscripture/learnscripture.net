from django.urls import reverse

from accounts.models import Identity
from bibleverses.models import VerseSet

from .base import FullBrowserTest, WebTestBase
from .test_bibleverses import RequireExampleVerseSetsMixin


class ViewSetTestsBase(RequireExampleVerseSetsMixin):

    def trigger_version_change(self):
        if self.is_full_browser_test:
            # Automatically triggered, just:
            self.wait_until_loaded('body')
        else:
            self.submit('#id-trigger-version-change')

    def test_change_version(self):
        identity, account = self.create_account()
        self.login(account)
        vs = VerseSet.objects.get(slug='bible-101')
        self.get_url('view_verse_set', slug=vs.slug)

        self.assertTextPresent("saith")

        self.fill({"#id-version-select": "NET"})
        self.trigger_version_change()

        self.assertTextPresent("replied")

    def test_learn_selected_version(self):
        identity, account = self.create_account()
        self.login(account)
        vs = VerseSet.objects.get(slug='bible-101')

        self.assertEqual(identity.verse_statuses.all().count(), 0)

        self.get_literal_url(reverse('view_verse_set', kwargs=dict(slug=vs.slug)) +
                             "?version=NET")
        self.submit("[name=learn]")

        # Can use 'all' here because this is the first time we've chosen anything
        verse_statuses = identity.verse_statuses.all()
        self.assertTrue(len(verse_statuses) > 0)
        self.assertTrue(all(uvs.version.slug == 'NET' for uvs in verse_statuses))

    def test_drop_from_queue(self):
        identity, account = self.create_account()
        self.login(account)
        vs = VerseSet.objects.get(slug='bible-101')
        identity.add_verse_set(vs)
        self.assertEqual(len(identity.bible_verse_statuses_for_learning(vs.id)),
                         vs.verse_choices.count())

        self.get_url('view_verse_set', slug=vs.slug)

        self.assertTextPresent("You have %d verses from this set in your queue" %
                               vs.verse_choices.count())

        self.submit("[name='drop']")

        self.assertEqual(len(identity.bible_verse_statuses_for_learning(vs.id)),
                         0)

    def test_view_without_identity(self):
        ids = list(Identity.objects.all())
        vs = VerseSet.objects.get(slug='bible-101')
        self.assertEqual(Identity.objects.exclude(id__in=[i.id for i in ids]).all().count(), 0)
        self.get_url('view_verse_set', slug=vs.slug)
        # Default version is NET:
        self.assertTextPresent("Jesus replied")
        self.assertTextPresent("John 14:6")

        # Shouldn't have created an Identity

        self.assertEqual(Identity.objects.exclude(id__in=[i.id for i in ids]).all().count(), 0)


class ViewSetTestsFB(ViewSetTestsBase, FullBrowserTest):
    pass


class ViewSetTestsWT(ViewSetTestsBase, WebTestBase):
    pass
