from __future__ import absolute_import

from autofixture import AutoFixture
from django.test import TestCase
from django.utils import timezone

from accounts.models import Account
from bibleverses.models import VerseSet, VerseSetType

class SearchTests(TestCase):

    def setUp(self):
        self.account = AutoFixture(Account).create(1)[0]

    def test_search_verse_set_title(self):
        vs1 = VerseSet.objects.create(name="For stupid people",
                                      slug="for-stupid-people",
                                      public=True,
                                      set_type=VerseSetType.SELECTION,
                                      created_by=self.account)
        vs2 = VerseSet.objects.create(name="For intelligent people",
                                      slug="for-intelligent-people",
                                      public=True,
                                      set_type=VerseSetType.SELECTION,
                                      created_by=self.account)

        results = VerseSet.objects.search(VerseSet.objects.all(),
                                          "Stupid")
        self.assertEqual(len(results), 1)
        self.assertIn("For stupid people", (v.name for v in results))
