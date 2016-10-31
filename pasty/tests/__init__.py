import contextlib
import os

import freezegun
import mock
from django.test import TestCase
from freezegun.api import FakeDatetime

from google.appengine.api import datastore_types
from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import ndb
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

        ndb.get_context().clear_cache()

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


@contextlib.contextmanager
def freeze_time(*args, **kwargs):
    # N.B. DOES NOT WORK AS A CLASS OR METHOD DECORATOR.
    # Make ndb work with freezegun. Without this it raises BadValueError when
    # validating the data for the datastore.
    # https://nvbn.github.io/2016/04/14/gae-datastore-freeze-time/

    dtypes = datastore_types

    with mock.patch('google.appengine.ext.db.DateTimeProperty.data_type', new=FakeDatetime):
        dtypes._VALIDATE_PROPERTY_VALUES[FakeDatetime] = dtypes.ValidatePropertyNothing
        dtypes._PACK_PROPERTY_VALUES[FakeDatetime] = dtypes.PackDatetime
        dtypes._PROPERTY_MEANINGS[FakeDatetime] = dtypes.entity_pb.Property.GD_WHEN

        with freezegun.freeze_time(*args, **kwargs):
            yield
