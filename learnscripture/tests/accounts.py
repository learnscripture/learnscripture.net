from __future__ import absolute_import

from django.test import TestCase

from accounts.models import Account


class AccountTests(TestCase):
    def test_password(self):
        acc = Account()
        acc.set_password('mypassword')
        self.assertTrue(acc.check_password('mypassword'))
        self.assertFalse(acc.check_password('123'))

