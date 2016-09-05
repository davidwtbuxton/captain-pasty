from django.test import TestCase

from google.appengine.ext import testbed


class AppEngineTestCase(TestCase):
    def setUp(self):
        super(AppEngineTestCase, self).setUp()

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_all_stubs()

    def tearDown(self):
        self.testbed.deactivate()

        super(AppEngineTestCase, self).tearDown()
