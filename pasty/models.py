import cloudstorage
from django.conf import settings
from django.db import models
from djangae import fields
from djangae.contrib.pagination import paginated_model
from google.appengine.api import app_identity

from . import utils


BUCKET_KEY = 'CLOUD_STORAGE_BUCKET'
language_choices = [(name, name) for name in utils.get_language_names()]


class Tag(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, primary_key=True)


@paginated_model(orderings=['created'])
class Paste(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    author = models.EmailField(blank=True)
    filename = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=200, blank=True)
    forked_from = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    tags = fields.SetField(models.SlugField(max_length=100), blank=True)
    files = fields.JSONField(default=list)
    summary = models.TextField(editable=False)

    def save_content(self, content, filename=None):
        # File contents are stored in Cloud Storage. The first file is
        # summarized and stored in the paste itself.  Paste.files is a list
        # of dicts, where each dict has a key for 'filename', and 'path',
        # with 'path' being the object name in Cloud Storage (minus the bucket).
        if not self.files:
            self.summary = utils.summarize_content(content, filename=filename)
            self.filename = filename

        path = store_content(content, filename, self)
        info = {'filename': filename, 'path': path}

        self.files.append(info)

        return self.save()


def get_bucket():
    """Returns the CLOUD_STORAGE_BUCKET from settings, or the default bucket."""
    custom_bucket = getattr(settings, BUCKET_KEY, u'')

    if custom_bucket:
        return custom_bucket
    else:
        return app_identity.get_default_gcs_bucket_name()


def store_content(content, filename, paste):
    """Creates a new object in Cloud Storage. Returns the name."""
    if isinstance(content, unicode):
        content = content.encode('utf-8')

    bucket = get_bucket()
    name = make_name_for_storage(filename, paste)
    dest = '/%s/%s' % (bucket, name)

    with cloudstorage.open(dest, 'w') as fh:
        fh.write(content)

    return name


def make_name_for_storage(filename, paste):
    """Returns a name for an object in Cloud Storage (without a bucket)."""
    # Like 'pasty/2016/03/01/1234567890/setup.py'.
    # BUG!!!! Need to handle 2 files with the same name for 1 paste.
    template = u'pasty/{dt:Y/M/d}/{pk}/{filename}'
    name = template.format(dt=paste.created, pk=paste.pk, filename=filename)
    # UTF-8 is valid, but the SDK stub can't handle non-ASCII characters.
    name = name.encode('utf-8')

    return name
