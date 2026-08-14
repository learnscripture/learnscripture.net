from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from bibleverses.models import MemoryStage, VerseSet

from .base import FullBrowserTest
from .test_bibleverses import RequireExampleVerseSetsMixin


class UserVersesPageTests(RequireExampleVerseSetsMixin, FullBrowserTest):
    def test_practice_button(self):
        identity, account = self.create_account()

        # Add a passage
        vs = VerseSet.objects.get(slug="psalm-23")
        vs.breaks = "BOOK18 23:4"
        vs.save()
        identity.add_verse_set(vs)

        # Make 'tested', but not needing revision
        identity.verse_statuses.update(
            strength=0.5,
            last_tested=timezone.now() - timedelta(days=10),
            next_test_due=timezone.now() + timedelta(days=1),
            memory_stage=MemoryStage.TESTED,
        )

        self.login(account)
        self.get_url("user_verses")

        for i in range(1, 7):
            self.assertTextPresent(f"Psalm 23:{i}")

        self.click('button[data-localized-reference="Psalm 23:2"]')

        # 'Practise verse' button
        assert self.get_element_text('button[name="reviewverse"]') == "Practise Psalm 23:2"

        # 'Practise section' button
        assert self.get_element_text('button[name="practisepassagesection"]') == "Practise section: Psalm 23:1-3"

        # 'Practise passage' button
        assert self.get_element_text('button[name="practisepassage"]') == "Practise passage: Psalm 23"

        self.submit('[name="practisepassagesection"]')

        self.assertUrlsEqual(reverse("learn"))
        self.assertTextPresent("Psalm 23:1")

        # Should be in 'practice' mode
        assert "PRACTICE" in self.get_element_text("#id-instructions")

        # Type the verse:
        words = "The LORD is my shepherd I shall not want"
        for word in words.split():
            self.fill({"#id-typing": word[0]})

        # Click next
        self.click("#id-next-btn")

        for i in [1, 2]:
            # Skip
            self.click("#id-verse-options-menu-btn")
            self.click("#id-skip-verse-btn")

        self.wait_for_ajax()

        # Should have gone back to where we came from
        self.wait_until_loaded("body.user-verses-page")
        self.assertUrlsEqual(reverse("user_verses"))
