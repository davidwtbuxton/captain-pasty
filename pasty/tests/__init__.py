from django.test import TestCase

from google.appengine.ext import testbed


class AppEngineTestCase(TestCase):
    def setUp(self):
        super(AppEngineTestCase, self).setUp()

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_app_identity_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_user_stub()
        self.testbed.init_search_stub()

    def tearDown(self):
        self.testbed.deactivate()

        super(AppEngineTestCase, self).tearDown()
