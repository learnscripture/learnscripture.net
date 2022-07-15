from .base import WebTestBase


class ContactFormTest(WebTestBase):
    def test_page(self):
        self.get_url("contact")
        self.assertTextPresent("contact@learnscripture.net")
