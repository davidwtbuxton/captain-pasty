import cloudstorage
from djangae import fields
from djangae.contrib.pagination import paginated_model
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils import encoding
from django.utils import safestring
from django.utils import timezone
from google.appengine.api import app_identity

from . import utils


BUCKET_KEY = 'CLOUD_STORAGE_BUCKET'
language_choices = [(name, name) for name in utils.get_language_names()]


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
    num_lines = models.BigIntegerField(blank=True, null=True)

    def content_highlight(self):
        """Returns the file content with syntax highlighting."""
        text = self.content.read()
        markup = utils.highlight_content(text, filename=self.filename)

        return safestring.mark_safe(markup)


@encoding.python_2_unicode_compatible
@paginated_model(orderings=['created'])
class Paste(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    author = models.EmailField(blank=True)
    filename = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=200, blank=True)
    forked_from = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    files = fields.RelatedListField(PastyFile)
    summary = models.TextField(editable=False)
    num_lines = models.BigIntegerField(null=True, blank=True)
    num_files = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        author = self.author or u'anonymous'
        name = self.filename or self.pk

        return u'%s / %s' % (author, name)

    def save(self, *args, **kwargs):
        files = list(self.files.all())
        self.num_files = len(files)
        self.num_lines = sum(f.num_lines or 0 for f in files)

        return super(Paste, self).save(*args, **kwargs)

    def save_content(self, content, filename=None):
        # File contents are stored in Cloud Storage. The first file is
        # summarized and stored in the paste itself.  Paste.files is a list
        # of dicts, where each dict has a key for 'filename', and 'path',
        # with 'path' being the object name in Cloud Storage (minus the bucket).
        if not self.files:
            self.summary = utils.summarize_content(content, filename=filename)
            self.filename = filename

        num_lines = utils.count_lines(content)
        pasty_file = PastyFile(filename=filename, num_lines=num_lines)
        pasty_file.content.save(filename, ContentFile(content))
        pasty_file.save()

        self.files.add(pasty_file)

        return self.save()

    def to_dict(self):
        """JSON representation."""
        info = {
            'id': self.pk,
            'created': self.created,
            'author': self.author,
            'filename': self.filename,
            'description': self.description,
            'forked_from': self.forked_from,
            'tags': self.tags,
            'files': [],
            'summary': self.summary,
        }

        for pasty_file in self.files.all():
            file_info = {
                'id': pasty_file.pk,
                'created': pasty_file.created,
                'filename': pasty_file.filename,
                'content': pasty_file.content.name,
                'link': pasty_file.content.url,
            }
            info['files'].append(file_info)

        return info



@paginated_model(orderings=['created'])
class Star(models.Model):
    id = models.CharField(max_length=250, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    author = models.EmailField()
    paste_id = models.BigIntegerField()


def get_starred_pastes(email):
    """Returns pastes starred by a user, ordered by when the paste was starred."""
    stars = Star.objects.filter(author=email).order_by('-created')
    paste_ids = [star.paste_id for star in stars[:20]]
    pastes = list(Paste.objects.filter(pk__in=paste_ids))
    pastes.sort(key=lambda x: paste_ids.index(x.pk))

    return pastes
