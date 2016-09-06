import cloudstorage
from djangae import fields
from djangae.contrib.pagination import paginated_model
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils import safestring
from django.utils import timezone
from google.appengine.api import app_identity

from . import utils


BUCKET_KEY = 'CLOUD_STORAGE_BUCKET'
language_choices = [(name, name) for name in utils.get_language_names()]


class Tag(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, primary_key=True)


def make_name_for_storage(instance, filename):
    """Returns a name for an object in Cloud Storage (without a bucket)."""
    # Like 'pasty/2016/03/01/1234567890/setup.py'.
    # BUG!!!! Need to handle 2 files with the same name for 1 paste.
    dt = timezone.now()
    template = u'pasty/{dt:%Y/%m/%d}/{filename}'
    name = template.format(dt=dt, filename=filename)
    # UTF-8 is valid, but the SDK stub can't handle non-ASCII characters.
    name = name.encode('utf-8')

    return name


class PastyFile(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=200, blank=True)
    content = models.FileField(upload_to=make_name_for_storage)

    def content_highlight(self):
        """Returns the file content with syntax highlighting."""
        text = self.content.read()
        markup = utils.highlight_content(text, filename=self.filename)

        return safestring.mark_safe(markup)


@paginated_model(orderings=['created'])
class Paste(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    author = models.EmailField(blank=True)
    filename = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=200, blank=True)
    forked_from = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    tags = fields.SetField(models.SlugField(max_length=100), blank=True)
    files = fields.RelatedListField(PastyFile)
    summary = models.TextField(editable=False)

    def save_content(self, content, filename=None):
        # File contents are stored in Cloud Storage. The first file is
        # summarized and stored in the paste itself.  Paste.files is a list
        # of dicts, where each dict has a key for 'filename', and 'path',
        # with 'path' being the object name in Cloud Storage (minus the bucket).
        if not self.files:
            self.summary = utils.summarize_content(content, filename=filename)
            self.filename = filename

        pasty_file = PastyFile(filename=filename)
        pasty_file.content.save(filename, ContentFile(content))
        pasty_file.save()

        self.files.add(pasty_file)

        return self.save()


