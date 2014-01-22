# -*- coding: utf-8 -*-
from __future__ import absolute_import

import unittest

from bibleverses.services import get_esv

__all__ = ['TestEsvService']

class TestEsvService(unittest.TestCase):

    def test_get_esv_single(self):
        d = get_esv(['John 3:16'])
        self.assertEqual(d, {'John 3:16': '"For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.'})

    def test_get_esv_multi(self):
        self.maxDiff = None
        d = get_esv(['Psalm 126:1', 'Psalm 126:2'])
        self.assertEqual(d, {'Psalm 126:1': '''When the LORD restored the fortunes of Zion,
we were like those who dream.''',
                             'Psalm 126:2': '''Then our mouth was filled with laughter,
and our tongue with shouts of joy;
then they said among the nations,
"The LORD has done great things for them."'''})
