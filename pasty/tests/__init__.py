import os

from django.test import TestCase

from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import testbed


class AppEngineTestCase(TestCase):
    def setUp(self):
        super(AppEngineTestCase, self).setUp()

        policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=1)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_app_identity_stub()
        self.testbed.init_datastore_v3_stub(consistency_policy=policy)
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_user_stub()
        self.testbed.init_search_stub()

    def tearDown(self):
        self.testbed.deactivate()

        super(AppEngineTestCase, self).tearDown()

    def login(self, email, user_id=None, is_admin=False):
        """Set the current Google authenticated user by email address.
        Use is_admin=True to set them as an App Engine admin.
        """
        user_id = user_id or email.split('@', 1)[0]
        os.environ['USER_EMAIL'] = email
        os.environ['USER_ID'] = user_id
        os.environ['USER_IS_ADMIN'] = '1' if is_admin else '0'

    def logout(self):
        for key in self._user_keys:
            del os.environ[key]
