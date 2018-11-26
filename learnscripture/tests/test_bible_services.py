# -*- coding: utf-8 -*-
import unittest2

from bibleverses.services import get_esv, search_esv

from .base import TestBase
from .test_bibleverses import SetupEsvMixin


class TestEsvService(unittest2.TestCase):

    def test_get_esv_single(self):
        d = list(get_esv(['John 3:16']))
        self.assertEqual(d, [('John 3:16', '"For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.')])

    def test_get_esv_multi(self):
        self.maxDiff = None
        d = list(get_esv(['Psalm 126:1', 'Psalm 126:2']))
        self.assertEqual(d, [('Psalm 126:1', '''When the LORD restored the fortunes of Zion,
we were like those who dream.'''),
                             ('Psalm 126:2', '''Then our mouth was filled with laughter,
and our tongue with shouts of joy;
then they said among the nations,
"The LORD has done great things for them."''')])


class TestEsvSearch(SetupEsvMixin, TestBase):

    def test_search(self):
        l, more_results = search_esv(self.esv, "God loved world gave", 0, 10)
        self.assertEqual(len(l), 1)
        v = l[0]
        self.assertEqual(v.localized_reference, "John 3:16")
        self.assertEqual(more_results, False)
