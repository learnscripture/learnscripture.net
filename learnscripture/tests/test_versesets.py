# -*- coding: utf-8 -*-
from bibleverses.models import VerseSet, VerseSetType

from .base import AccountTestMixin, BibleVersesMixin, TestBase


class VerseSetTests(BibleVersesMixin, AccountTestMixin, TestBase):

    def test_visibility(self):
        _, creator = self.create_account(username='creator')
        _, viewer = self.create_account(username='viewer')

        vs = VerseSet.objects.create(name="My set",
                                     slug="my-set",
                                     created_by=creator,
                                     language_code='en',
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

    def test_smart_name(self):
        vs1 = VerseSet(name="Psalm 23",
                       language_code='en',
                       set_type=VerseSetType.PASSAGE)
        self.assertEqual(vs1.smart_name('en'), 'Psalm 23')
        self.assertEqual(vs1.smart_name('tr'), 'Mezmur 23')

        vs2 = VerseSet(name="Hebrews 1:1-10",
                       language_code='en',
                       set_type=VerseSetType.PASSAGE)
        self.assertEqual(vs2.smart_name('en'), 'Hebrews 1:1-10')
        self.assertEqual(vs2.smart_name('tr'), 'İbraniler 1:1-10')

        vs3 = VerseSet(name="Romans 8 - wonderful promises!",
                       language_code='en',
                       set_type=VerseSetType.PASSAGE)
        self.assertEqual(vs3.smart_name('en'), 'Romans 8 - wonderful promises!')
        self.assertEqual(vs3.smart_name('tr'), 'Romans 8 - wonderful promises! (Romalılar 8)')

        vs4 = VerseSet(name="Mark 01:01-09",
                       language_code='en',
                       set_type=VerseSetType.PASSAGE)
        self.assertEqual(vs4.smart_name('en'), 'Mark 01:01-09')
        self.assertEqual(vs4.smart_name('tr'), 'Markos 1:1-9')

        vs5 = VerseSet(name="Psalm 37: 1 - 40",
                       language_code='en',
                       set_type=VerseSetType.PASSAGE)
        self.assertEqual(vs5.smart_name('en'), 'Psalm 37: 1 - 40')
        self.assertEqual(vs5.smart_name('tr'), 'Mezmur 37:1-40')

    def test_smart_name_no_abbreviations(self):
        # 'Promises' starts with 'pro' == abbreviation for proverbs. We should
        # not treat this the same as 'Proverbs'
        vs1 = VerseSet(name="Promises!",
                       language_code='en',
                       set_type=VerseSetType.PASSAGE)
        self.assertEqual(vs1.smart_name('en'), 'Promises!')
        self.assertEqual(vs1.smart_name('tr'), 'Promises!')

    def test_smart_name_remainder(self):
        vs1 = VerseSet(name="Marked",
                       language_code='en',
                       set_type=VerseSetType.PASSAGE)
        self.assertEqual(vs1.smart_name('en'), 'Marked')
        self.assertEqual(vs1.smart_name('tr'), 'Marked')
