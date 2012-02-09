from django.utils import unittest
from django.template import RequestContext
from django.test.client import RequestFactory

from learnscripture.utils.context import lazy_dict

class TestLazyDict(unittest.TestCase):
    def setUp(self):
        super(TestLazyDict, self).setUp()
        self.factory = RequestFactory()

    def test_lazy(self):
        done = []
        def processor(request):
            done.append(True)
            return {'key1': 'val1'}


        request = self.factory.get('/')
        c = RequestContext(request, {'otherkey': 'val2'}, processors=[lazy_dict(processor, ['key1'])])

        self.assertTrue(len(done) == 0)

        v = c['otherkey']
        self.assertTrue(len(done) == 0)

        self.assertRaises(KeyError, lambda: c['nonexistant'])

        self.assertTrue(len(done) == 0)

        v = c['key1']
        self.assertTrue(len(done) == 1)

        self.assertTrue(v, 'val1')

        # Shouldn't call it twice
        v = c['key1']
        self.assertTrue(len(done) == 1)

