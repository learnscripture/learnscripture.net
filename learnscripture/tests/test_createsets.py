# -*- coding: utf-8 -*-
import time

from awards.models import AwardType
from bibleverses.languages import LANGUAGE_CODE_EN
from bibleverses.models import StageType, TextVersion, VerseSet, VerseSetType
from events.models import Event, EventType

from .base import BibleVersesMixin, FullBrowserTest


class CreateSetTests(BibleVersesMixin, FullBrowserTest):

    browser_window_size = (1024, 1200)

    def setUp(self):
        super(CreateSetTests, self).setUp()
        self._identity, self._account = self.create_account()

    def _add_ref(self, ref):
        self.fill({"#id_quick_find": ref})
        self.click("#id_lookup")
        self.click(".btn.add-to-set")
        self.wait_until_loaded('#id-verse-list tbody tr td')
        time.sleep(0.1)

    def test_create_selection_set(self):
        self.login(self._account)
        self.get_url('create_selection_set')
        self.fill({"#id_name": "My set",
                   "#id_description": "My description"})
        self._add_ref("Gen 1:5")
        self.assertTextPresent("And God called the light Day")

        self.fill({"#id_public": True})
        self.submit("#id-save-btn")
        self.assertTrue(self.get_page_title().startswith("Verse set: My set"))
        self.assertTextPresent("And God called the light Day")

        self.assertEqual(self._account.awards.filter(award_type=AwardType.SHARER).count(),
                         1)
        self.assertEqual(Event.objects.filter(event_type=EventType.VERSE_SET_CREATED).count(),
                         1)
        vs = VerseSet.objects.get()
        self.assertEqual(vs.name, "My set")
        self.assertEqual(vs.language_code, "en")

    def test_create_selection_set_combos(self):
        self.login(self._account)
        self.get_url('create_selection_set')
        self.fill({"#id_name": "My set"})
        self._add_ref("Gen 1:1-2")
        self._add_ref("Gen 1:4")

        self.fill({"#id_public": True})
        self.submit("#id-save-btn")
        self.assertTrue(self.get_page_title().startswith("Verse set: My set"))
        self.assertTextPresent("In the beginning")

        vs = VerseSet.objects.get()
        # Check editing doesn't break it
        self.get_url('edit_set', slug=vs.slug)
        self.submit("#id-save-btn")

        vs = VerseSet.objects.get()
        self.assertEqual([vc.internal_reference for vc in vs.verse_choices.all()],
                         ["BOOK0 1:1-2", "BOOK0 1:4"])

    def test_dedupe_selection_sets(self):
        self.login(self._account)
        self.get_url("create_selection_set")
        self.fill({"#id_name": "My set"})

        # Add Gen 1:5
        self._add_ref("Genesis 1:5")

        self.submit("#id-save-btn")

        vs = VerseSet.objects.get(name='My set')
        self.assertEqual(len(vs.verse_choices.all()), 1)

        current_localized_reference_list = [("Genesis 1:5", 0)]

        def _add_new_ref(ref):
            # Edit again
            self.get_url('edit_set', slug=vs.slug)
            self._add_ref(ref)

            self.submit("#id-save-btn")

            self.assertTextPresent("Verse set 'My set' saved")  # Checks we didn't get 500

            if ref not in [r for r, i in current_localized_reference_list]:
                current_localized_reference_list.append((ref, len(current_localized_reference_list)))

            self.assertEqual(current_localized_reference_list,
                             sorted([(vc.get_localized_reference(LANGUAGE_CODE_EN), vc.set_order)
                                     for vc in vs.verse_choices.all()]))

        # Caching could cause these to fail
        _add_new_ref("Genesis 1:6")
        _add_new_ref("Genesis 1:6")
        _add_new_ref("Genesis 1:7")
        _add_new_ref("Genesis 1:7")

    def test_forget_name(self):
        """
        If they forget the name, it should not validate,
        but shouldn't forget the verse list
        """
        self.login(self._account)
        self.get_url('create_selection_set')

        self._add_ref("Gen 1:5")
        self._add_ref("Gen 1:6")

        self.submit("#id-save-btn")

        self.assertTrue(self.get_page_title().startswith("Create selection set"))
        self.assertTextPresent("This field is required")
        self.assertTextPresent("Genesis 1:5")
        self.assertTextPresent("Genesis 1:6")

    def test_edit(self):
        vs = VerseSet.objects.create(created_by=self._account,
                                     set_type=VerseSetType.SELECTION,
                                     language_code='en',
                                     name='my set')
        vc1 = vs.verse_choices.create(internal_reference='BOOK0 1:1',
                                      set_order=0)
        vc2 = vs.verse_choices.create(internal_reference='BOOK0 1:5',
                                      set_order=1)
        vc3 = vs.verse_choices.create(internal_reference='BOOK0 1:10',
                                      set_order=2)
        self.login(self._account)
        self.get_url('edit_set', slug=vs.slug)
        self.drag_and_drop("#id-verse-list tbody tr:nth-child(2)",
                           "#id-verse-list thead tr")
        self.submit("#id-save-btn")

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all()
        self.assertEqual(sorted(vc.id for vc in vcs), sorted([vc1.id, vc2.id, vc3.id]))
        self.assertEqual(vs.verse_choices.get(internal_reference='BOOK0 1:1').set_order, 1)
        self.assertEqual(vs.verse_choices.get(internal_reference='BOOK0 1:5').set_order, 0)

    def test_remove(self):
        self.login(self._account)
        vs = VerseSet.objects.create(created_by=self._account,
                                     language_code='en',
                                     set_type=VerseSetType.SELECTION,
                                     name='my set')
        vs.verse_choices.create(internal_reference='BOOK0 1:1',
                                set_order=0)
        vc2 = vs.verse_choices.create(internal_reference='BOOK0 1:5',
                                      set_order=1)

        identity = self._identity
        # Record some learning against the verse we will remove
        identity.add_verse_set(vs)
        identity.record_verse_action('Genesis 1:1', 'KJV', StageType.TEST, 1.0)

        self.get_url('edit_set', slug=vs.slug)
        self.click("#id-verse-list tbody tr:first-child td .icon-trash")
        self.submit("#id-save-btn")

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all()
        self.assertEqual([vc.id for vc in vcs], [vc2.id])

        # Need to ensure that the UVS has not been deleted
        identity.verse_statuses.get(version__slug='KJV', localized_reference='Genesis 1:1')

    def test_require_account(self):
        self.get_url('create_selection_set')
        self.set_preferences()
        self.assertTextPresent('You need to')
        self.assertTextPresent('create an account')

    def test_create_passage_set(self):
        self.login(self._account)
        self.get_url('create_passage_set')

        self.fill({"#id_name": "Genesis 1:1-10"})
        self.fill({"#id_description": "My description"})

        self.fill({"#id_quick_find": "Gen 1:1-10"})
        self.click("#id_lookup")
        self.wait_until_loaded('#id-verse-list tbody tr td')
        self.assertTextPresent("And God called the light Day")

        # Check boxes for Genesis 1:3, 1:9
        self.click('#id-verse-list tbody tr:nth-child(3) input')
        self.click('#id-verse-list tbody tr:nth-child(9) input')

        self.submit("#id-save-btn")
        self.assertTrue(self.get_page_title().startswith("Verse set: Genesis 1"))
        self.assertTextPresent("And God called the light Day")

        vs = VerseSet.objects.get(name='Genesis 1:1-10',
                                  set_type=VerseSetType.PASSAGE)
        self.assertTrue(len(vs.verse_choices.all()), 10)
        self.assertEqual(vs.breaks, "BOOK0 1:3,BOOK0 1:9")
        self.assertEqual(vs.passage_id, 'BOOK0 1:1-10')
        self.assertEqual(vs.language_code, 'en')

    def test_create_passage_set_merged(self):
        # This tests a whole bunch of problems regarding creating/editing
        # passage verse sets in different versions due to merged verses.
        refs = {
            'NET': 'Romans 3:24-27',
            'TCL02': 'Romalılar 3:24-27',
        }
        verses = {
            'NET': [
                ("Romans 3:24", "But they are justified freely"),
                ("Romans 3:25", "God publicly displayed him"),
                ("Romans 3:26", "This was also to demonstrate his righteousness"),
                ("Romans 3:27", "Where, then, is boasting?"),
            ],
            'TCL02': [
                ("Romalılar 3:24", "İnsanlar İsa Mesih'te olan kurtuluşla"),
                ("Romalılar 3:25-26", "Tanrı Mesih'i, kanıyla günahları bağışlatan"),
                ("Romalılar 3:27", "Öyleyse neyle övünebiliriz?"),
            ]
        }
        titles = refs

        # Tests for creating with a version that has merged verses.
        for default_version in ('NET', 'TCL02'):
            with self.subTest(default_version=default_version):
                for display_version in ('NET', 'TCL02'):
                    with self.subTest(display_version=display_version):
                        VerseSet.objects.all().delete()
                        self._identity.default_bible_version = TextVersion.objects.get(slug=default_version)
                        self._identity.save()
                        self.login(self._account)
                        self.get_url('create_passage_set')

                        self.fill({"#id-version-select": display_version})
                        self.fill({"#id_quick_find": refs[display_version]})
                        self.click("#id_lookup")
                        self.wait_until_loaded('#id-verse-list tbody tr td')

                        for verse_ref, verse_text in verses[display_version]:
                            self.assertTextPresent(verse_ref)
                            self.assertTextPresent(verse_text)

                        # Check box for Romalılar 3:25-26 or Romans 3:25
                        self.click('#id-verse-list tbody tr:nth-child(2) input')

                        self.submit("#id-save-btn")

                        # We should have saved something:
                        vs = VerseSet.objects.get(name=titles[display_version],
                                                  set_type=VerseSetType.PASSAGE)

                        # We're on the view page:
                        self.assertTrue(self.get_page_title().startswith("Verse set: " + titles[default_version]))

                        # VerseSet will be as neutral as possible, so has unmerged verses.
                        self.assertEqual([vc.internal_reference for vc in vs.verse_choices.all()],
                                         ['BOOK44 3:24', 'BOOK44 3:25', 'BOOK44 3:26', 'BOOK44 3:27'])
                        self.assertEqual(vs.breaks, "BOOK44 3:25")
                        self.assertEqual(vs.passage_id, 'BOOK44 3:24-27')

                        # We should be able to edit again:
                        self.get_url('edit_set', slug=vs.slug)
                        for verse_ref, verse_text in verses[default_version]:
                            self.assertTextPresent(verse_ref)
                            self.assertTextPresent(verse_text)

    def test_create_duplicate_passage_set(self):
        self.test_create_passage_set()
        self.get_url("create_passage_set")
        self.fill({"#id_quick_find": "Gen 1:1-10"})

        self.click("#id_lookup")
        self.wait_until_loaded('#id-verse-list tbody tr td')
        self.assertTextPresent("There are already")

    def test_empty_passage_set(self):
        self.login(self._account)
        self.get_url("create_passage_set")
        self.fill({"#id_name": "xxx"})
        self.click("#id-save-btn")
        self.assertTextPresent("No verses in set")

    def test_edit_passage_set(self):
        self.login(self._account)
        vs = VerseSet.objects.create(created_by=self._account,
                                     language_code='en',
                                     set_type=VerseSetType.PASSAGE,
                                     name='Psalm 23',
                                     breaks="BOOK18 23:5")
        internal_references = []
        for i in range(1, 7):
            ref = 'BOOK18 23:%d' % i
            internal_references.append(ref)
            vs.verse_choices.create(internal_reference=ref,
                                    set_order=i - 1)

        # Simple test - editing and pressing save should leave
        # everything the same.
        self.get_url('edit_set', slug=vs.slug)
        self.submit("#id-save-btn")

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all().order_by('set_order')
        self.assertEqual([vc.internal_reference for vc in vcs],
                         internal_references)
        self.assertEqual(vs.breaks, "BOOK18 23:5")
