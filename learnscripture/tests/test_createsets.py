# -*- coding: utf-8 -*-
import time

from awards.models import AwardType
from bibleverses.languages import LANGUAGE_CODE_EN
from bibleverses.models import StageType, TextVersion, VerseSet, VerseSetType
from events.models import Event, EventType

from .base import FullBrowserTest


class CreateSetTests(FullBrowserTest):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def setUp(self):
        super(CreateSetTests, self).setUp()
        self._identity, self._account = self.create_account()

    def _add_ref(self, ref):
        self.fill({"#id_quick_find": ref})
        self.click("#id_lookup")
        self.click("input.add-to-set")
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

    def test_dedupe_selection_sets(self):
        self.login(self._account)
        self.get_url("create_selection_set")
        self.fill({"#id_name": "My set"})

        # Add Gen 1:5
        self._add_ref("Genesis 1:5")

        self.click("#id-save-btn")

        vs = VerseSet.objects.get(name='My set')
        self.assertEqual(len(vs.verse_choices.all()), 1)

        current_localized_reference_list = [("Genesis 1:5", 0)]

        def _add_new_ref(ref):
            # Edit again
            self.get_url('edit_set', slug=vs.slug)
            self._add_ref(ref)

            self.click("#id-save-btn")

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
                                     name='my set')
        vc1 = vs.verse_choices.create(internal_reference='BOOK0 1:1',
                                      set_order=0)
        vc2 = vs.verse_choices.create(internal_reference='BOOK0 1:5',
                                      set_order=1)
        vc3 = vs.verse_choices.create(internal_reference='BOOK0 1:10',
                                      set_order=2)
        self.login(self._account)
        self.get_url('edit_set', slug=vs.slug)
        self.drag_and_drop_by_offset("#id-verse-list tbody tr:first-child td",
                                     0, 60)
        self.submit("#id-save-btn")

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all()
        self.assertEqual(sorted(vc.id for vc in vcs), sorted([vc1.id, vc2.id, vc3.id]))
        self.assertEqual(vs.verse_choices.get(internal_reference='BOOK0 1:1').set_order, 1)
        self.assertEqual(vs.verse_choices.get(internal_reference='BOOK0 1:5').set_order, 0)

    def test_remove(self):
        self.login(self._account)
        vs = VerseSet.objects.create(created_by=self._account,
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
        self.click("#id-save-btn")

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

        self.click("#id-save-btn")
        self.assertTrue(self.get_page_title().startswith("Verse set: Genesis 1"))
        self.assertTextPresent("And God called the light Day")

        vs = VerseSet.objects.get(name='Genesis 1:1-10',
                                  set_type=VerseSetType.PASSAGE)
        self.assertTrue(len(vs.verse_choices.all()), 10)
        self.assertEqual(vs.breaks, "BOOK0 1:3,BOOK0 1:9")
        self.assertEqual(vs.passage_id, 'BOOK0 1:1-10')

    def test_create_passage_set_merged(self):
        # Tests for creating with a version that has merged verses
        self._identity.default_bible_version = TextVersion.objects.get(slug='TCL02')
        self._identity.save()
        self.login(self._account)
        self.get_url('create_passage_set')

        self.fill({"#id_quick_find": "Romalılar 3:24-27"})
        self.click("#id_lookup")
        self.wait_until_loaded('#id-verse-list tbody tr td')

        # Displayed verses will have to shown merged verses:
        self.assertTextPresent("Romalılar 3:24")
        self.assertTextPresent("İnsanlar İsa Mesih'te olan kurtuluşla")
        self.assertTextPresent("Romalılar 3:25-26")
        self.assertTextPresent("Tanrı Mesih'i, kanıyla günahları bağışlatan")
        self.assertTextPresent("Romalılar 3:27")
        self.assertTextPresent("Öyleyse neyle övünebiliriz?")

        # Check boxes for Rom 3:25-26
        self.click('#id-verse-list tbody tr:nth-child(2) input')

        self.click("#id-save-btn")

        self.assertTrue(self.get_page_title().startswith("Verse set: Romalılar 3:24-27"))

        # VerseSet will be as neutral as possible, so has unmerged verses.
        vs = VerseSet.objects.get(name='Romalılar 3:24-27',
                                  set_type=VerseSetType.PASSAGE)
        self.assertEqual([vc.internal_reference for vc in vs.verse_choices.all()],
                         ['BOOK44 3:24', 'BOOK44 3:25', 'BOOK44 3:26', 'BOOK44 3:27'])
        self.assertEqual(vs.breaks, "BOOK44 3:25")
        self.assertEqual(vs.passage_id, 'BOOK44 3:24-27')

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
        self.click("#id-save-btn")

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all().order_by('set_order')
        self.assertEqual([vc.internal_reference for vc in vcs],
                         internal_references)
        self.assertEqual(vs.breaks, "BOOK18 23:5")
