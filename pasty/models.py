import cloudstorage
from django.core.urlresolvers import reverse
from django.utils import safestring
from django.utils import timezone
from google.appengine.api import app_identity
from google.appengine.ext import ndb
from . import utils


BUCKET_KEY = 'CLOUD_STORAGE_BUCKET'
language_choices = [(name, name) for name in utils.get_language_names()]


def make_name_for_storage(paste, filename):
    """Returns a name for an object in Cloud Storage (without a bucket)."""
    # Like 'pasty/2016/03/01/1234567890/setup.py'.
    # BUG!!!! Need to handle 2 files with the same name for 1 paste.
    dt = timezone.now()
    template = u'pasty/{dt:%Y/%m/%d}/{id}/{filename}'
    name = template.format(dt=dt, id=paste.key.id(), filename=filename)
    # UTF-8 is valid, but the SDK stub can't handle non-ASCII characters.
    name = name.encode('utf-8')

    return name


class PastyFile(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    filename = ndb.StringProperty()
    path = ndb.StringProperty()
    num_lines = ndb.IntegerProperty(default=0)

    def content_highlight(self):
        """Returns the file content with syntax highlighting."""
        with self.open('r') as fh:
            text = fh.read()

        markup = utils.highlight_content(text, filename=self.filename)

        return safestring.mark_safe(markup)

    @classmethod
    def bucket_path(cls, path):
        bucket = app_identity.get_default_gcs_bucket_name()

        return '/%s/%s' % (bucket, path)

    @classmethod
    def from_content(self, paste, filename, content):
        """Save the content to cloud storage and return a new PastyFile."""
        num_lines = utils.count_lines(content)
        path = make_name_for_storage(paste, filename)

        if isinstance(content, unicode):
            content = content.encode('utf-8')

        obj = PastyFile(filename=filename, path=path, num_lines=num_lines)

        with obj.open('w') as fh:
            fh.write(content)

        return obj

    def open(self, mode='r'):
        path = self.bucket_path(self.path)

        return cloudstorage.open(path, mode)



class Paste(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    author = ndb.StringProperty()
    filename = ndb.StringProperty()
    description = ndb.StringProperty()
    forked_from = ndb.KeyProperty(kind='Paste')
    files = ndb.LocalStructuredProperty(PastyFile, repeated=True)
    preview = ndb.TextProperty()

    def __unicode__(self):
        return u'%s / %s' % (self.author, self.filename)

    @ndb.ComputedProperty
    def num_files(self):
        return len(self.files)

    @ndb.ComputedProperty
    def num_lines(self):
        return sum(pasty_file.num_lines for pasty_file in self.files)

    @property
    def download_url(self):
        return reverse('paste_download', self.key.id())

    def save_content(self, content, filename=None):
        # File contents are stored in Cloud Storage. The first file is
        # summarized and stored in the paste itself.  Paste.files is a list
        # of dicts, where each dict has a key for 'filename', and 'path',
        # with 'path' being the object name in Cloud Storage (minus the bucket).
        if not self.files:
            self.preview = utils.summarize_content(content, filename=filename)
            self.filename = filename

        pasty_file = PastyFile.from_content(
            self,
            filename=filename,
            content=content,
        )

        self.files.append(pasty_file)

        return self.put()

class Star(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    author = ndb.StringProperty(indexed=True)
    paste = ndb.KeyProperty(Paste)


def get_starred_pastes(email):
    """Returns pastes starred by a user, ordered by when the paste was starred."""
    stars = Star.query().filter(Star.author==email).order(-Star.created).fetch(100)
    keys = [star.paste for star in stars]
    pastes = [key.get() for key in keys]
    pastes.sort(key=lambda x: keys.index(x.key))

    return pastes
