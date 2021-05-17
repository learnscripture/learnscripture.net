from django.core import mail

from .base import WebTestBase


class ContactFormTest(WebTestBase):
    def test_success(self):
        self.get_url('contact')
        self.fill({
            '#id_message': 'Your site sucks',
        })
        self.submit('[name=send]')
        self.assertTextPresent('Thanks for your message')

        assert len(mail.outbox) == 1
        message = mail.outbox[0].body
        assert 'Your site sucks' in message
