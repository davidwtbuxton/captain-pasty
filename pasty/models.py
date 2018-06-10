import mimetypes
import os.path
import re

import cloudstorage
from django.http import Http404
from django.urls import reverse
from django.utils import safestring
from django.utils import text
from django.utils import timezone
from google.appengine.api import app_identity
from google.appengine.ext import ndb
from . import utils


BUCKET_KEY = 'CLOUD_STORAGE_BUCKET'
language_choices = [(name, name) for name in utils.get_language_names()]


class LexerConfig(ndb.Model):
    """Global config for customising what highlighting to use per file type."""
    class mapping(ndb.Model):
        extension = ndb.StringProperty(required=True)
        language = ndb.StringProperty(required=True)

    lexers = ndb.LocalStructuredProperty(mapping, repeated=True)

    @classmethod
    def get(cls):
        """Singleton method to get/create the configuration objects."""
        return cls.get_or_insert('config', lexers=[])

    @classmethod
    def get_config(cls):
        """Singleton method to get a map of extensions to languages."""
        config = cls.get()
        mapping = {obj.extension: obj.language for obj in config.lexers}

        return mapping


def make_name_for_storage(paste_id, filename, n, dt):
    """Returns a name for an object in Cloud Storage (without a bucket)."""
    # Like 'pasty/2016/03/01/1234567890/1-setup.py'.
    filename = os.path.normpath(filename)
    filename = text.get_valid_filename(filename)

    template = u'pasty/{dt:%Y/%m/%d}/{id}/{n}/{filename}'
    name = template.format(dt=dt, id=paste_id, n=n, filename=filename)
    # UTF-8 is valid, but the SDK stub can't handle non-ASCII characters.
    name = name.encode('utf-8')

    return name


def make_relative_path(path):
    """Returns the path for a file, relative to the paste ID.

    >>> make_relative_path('pasty/1999/12/31/123/1/foo.html')
    '1/foo.html'
    """
    match = re.search(r'^pasty/\d{4}/\d{1,2}/\d{1,2}/\d+/(.*)', path)

    if match:
        return match.group(1)
    else:
        raise ValueError('Invalid file path')


class PastyFile(ndb.Model):
    DEFAULT_CONTENT_TYPE = 'text/plain'
    DEFAULT_FILENAME = u'untitled.txt'

    created = ndb.DateTimeProperty(auto_now_add=True)
    filename = ndb.StringProperty(required=True)
    path = ndb.StringProperty()
    relative_path = ndb.StringProperty()
    num_lines = ndb.IntegerProperty(default=0)

    def content_highlight(self):
        """Returns the file content with syntax highlighting."""
        with self.open('r') as fh:
            text = fh.read()

        config = LexerConfig.get_config()
        _, markup = utils.highlight_content(text, filename=self.filename, config=config)

        return safestring.mark_safe(markup)

    def bucket_path(self):
        bucket = app_identity.get_default_gcs_bucket_name()

        return '/%s/%s' % (bucket, self.path)

    @classmethod
    def create(cls, filename, content, path, relative_path, num_lines):
        """Save the content to cloud storage and return a new PastyFile."""
        if isinstance(content, unicode):
            content = content.encode('utf-8')

        pfile = cls(
            filename=filename, path=path, relative_path=relative_path,
            num_lines=num_lines)

        with pfile.open('w') as fh:
            fh.write(content)

        return pfile

    @ndb.ComputedProperty
    def content_type(self):
        filename = self.filename or ''
        content_type, _ = mimetypes.guess_type(filename)

        return content_type or self.DEFAULT_CONTENT_TYPE

    def open(self, mode='r'):
        path = self.bucket_path()

        return cloudstorage.open(path, mode)


class Paste(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    author = ndb.StringProperty()
    filename = ndb.StringProperty(required=True, default=PastyFile.DEFAULT_FILENAME)
    description = ndb.StringProperty()
    fork = ndb.KeyProperty(kind='Paste')
    files = ndb.LocalStructuredProperty(PastyFile, repeated=True)
    preview = ndb.TextProperty()

    def __unicode__(self):
        author = self.author if self.author else u'anonymous'

        return u'%s / %s' % (author, self.filename)

    @classmethod
    def create_with_files(cls, files, **kwargs):
        """Creates a new Paste and saves files in storage."""
        fork = kwargs.get('fork')

        if fork:
            kwargs['fork'] = fork.key

        # OK. We need to create the Paste, then we can save the files to storage
        # (because the storage name includes the paste's ID), then we update
        # the paste again with the saved files' information.
        paste = Paste(**kwargs)
        paste.put()

        right_now = timezone.now()
        paste_id = paste.key.id()
        config = LexerConfig.get_config()

        # files is a sequence of (filename, content) pairs. But filename can
        # be '', in which case we choose a name based on the content's format
        # (e.g. if it looks like CSS, we choose 'untitled.css').
        for n, filename_content in enumerate(files, 1):
            filename, content = filename_content

            # If no filename, we pick one.
            if not filename:
                lexer = utils.choose_lexer(content)
                ext = utils.ext_for_lexer(lexer)
                filename = PastyFile.DEFAULT_FILENAME.replace('.txt', ext)

            num_lines = utils.count_lines(content)
            path = make_name_for_storage(paste_id, filename, n, right_now)
            relative_path = make_relative_path(path)

            pfile = PastyFile.create(
                filename=filename, content=content, path=path,
                num_lines=num_lines, relative_path=relative_path)
            paste.files.append(pfile)

        if files:
            # The first file is used to set the paste's own filename and
            # preview.
            fname = paste.files[0].filename
            _, content = files[0]
            _, preview = utils.summarize_content(content, filename=fname, config=config)
            paste.preview = preview
            paste.filename = fname

        paste.put()

        return paste


    @classmethod
    def get_or_404(cls, paste_id):
        """Returns a paste object. Raises Http404 if the paste_id is invalid."""
        try:
            paste_id = int(paste_id)
        except (ValueError, TypeError):
            raise Http404

        paste = cls.get_by_id(paste_id)

        if not paste:
            raise Http404

        return paste

    @ndb.ComputedProperty
    def num_files(self):
        return len(self.files)

    @ndb.ComputedProperty
    def num_lines(self):
        return sum(pasty_file.num_lines for pasty_file in self.files)

    @property
    def url(self):
        url = reverse('paste_detail', args=[self.key.id()])

        return url

    def to_dict(self):
        # Avoid problems when JSON-ifying a forked paste.
        obj = super(Paste, self).to_dict()
        obj['id'] = self.key.id()
        obj['url'] = self.url

        if obj['fork']:
            obj['fork'] = obj['fork'].id()

        return obj

    def create_star_for_author(self, author):
        """Helper to get/create a Star for this paste."""
        return Star.create(author, self)


class Star(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    author = ndb.StringProperty(indexed=True)
    paste = ndb.KeyProperty(Paste)

    @classmethod
    def create(self, author, paste):
        # We construct the star id ourselves so that if you star something
        # twice it doesn't create multiple stars for the same paste.
        star_id = u'%s/%s' % (author, paste.key.id())
        star = Star.get_or_insert(star_id, author=author, paste=paste.key)

        return star


class Peeling(ndb.Model):
    """Legacy model for converting old peelings to new pastes."""
    @classmethod
    def _get_kind(cls):
        return 'pastes_paste'


def get_starred_pastes(email):
    """Returns pastes starred by a user, ordered by when the paste was starred."""
    stars = Star.query().filter(Star.author==email).order(-Star.created).fetch(100)
    keys = [star.paste for star in stars]
    pastes = [key.get() for key in keys]
    pastes.sort(key=lambda x: keys.index(x.key))

    return pastes
