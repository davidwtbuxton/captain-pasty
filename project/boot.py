from django.utils.crypto import get_random_string
from google.appengine.ext import ndb


class AppConfig(ndb.Model):
    secret_key = ndb.StringProperty()

    @classmethod
    def get(cls):
        """Singleton configuration to store the Django secret key."""
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        secret_key = get_random_string(50, chars)

        return cls.get_or_insert('config', secret_key=secret_key)
