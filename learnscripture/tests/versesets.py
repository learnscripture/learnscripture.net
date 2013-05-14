from __future__ import absolute_import

from django.test import TestCase

from bibleverses.models import VerseSet, VerseSetType

from .base import AccountTestMixin

class VerseSetTests(AccountTestMixin, TestCase):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def test_visibility(self):
        _, creator = self.create_account(username='creator')
        _, viewer = self.create_account(username='viewer')

        vs = VerseSet.objects.create(name="My set",
                                     slug="my-set",
                                     created_by=creator,
                                     set_type=VerseSetType.SELECTION,
                                     public=False)

        # Private groups are visible to creator
        self.assertIn(vs,
                      VerseSet.objects.visible_for_account(creator)
                      )

        # But not to others.
        self.assertNotIn(vs,
                         VerseSet.objects.visible_for_account(viewer)
                         )

        vs.public = True
        vs.save()

        # public sets are visible
        self.assertIn(vs,
                      VerseSet.objects.visible_for_account(viewer)
                      )


        # hellbanned users
        creator.is_hellbanned = True
        creator.save()

        # Shouldn't be visible to others
        self.assertNotIn(vs,
                         VerseSet.objects.visible_for_account(viewer)
                         )
