import unittest

import pytest

from bibleverses.services import get_esv_v2, search_esv_v2

from .base import TestBase
from .test_bibleverses import SetupEsvMixin


@pytest.mark.skip(reason="ESV v2 is discontinued")
class TestEsvService(unittest.TestCase):
    def test_get_esv_v2_single(self):
        d = list(get_esv_v2(["John 3:16"]))
        assert d == [
            (
                "John 3:16",
                '"For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.',
            )
        ]

    def test_get_esv_v2_multi(self):
        self.maxDiff = None
        d = list(get_esv_v2(["Psalm 126:1", "Psalm 126:2"]))
        assert d == [
            (
                "Psalm 126:1",
                """When the LORD restored the fortunes of Zion,
we were like those who dream.""",
            ),
            (
                "Psalm 126:2",
                '''Then our mouth was filled with laughter,
and our tongue with shouts of joy;
then they said among the nations,
"The LORD has done great things for them."''',
            ),
        ]


@pytest.mark.skip(reason="ESV v2 is discontinued")
class TestEsvSearch(SetupEsvMixin, TestBase):
    def test_search(self):
        l, more_results = search_esv_v2(self.esv, "God loved world gave", 0, 10)
        assert len(l) == 1
        v = l[0]
        assert v.localized_reference == "John 3:16"
        assert not more_results
        assert (
            "“For **God** so **loved** the **world**, that he **gave** his only Son, that whoever believes in him should"
            in v.verses[0].text_saved
        )
