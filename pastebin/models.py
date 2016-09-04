from django.db import models
from djangae import fields
from djangae.contrib.pagination import paginated_model

from . import utils


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
    content = models.TextField()
    content_highlight = models.TextField(editable=False)
    content_summary = models.TextField(editable=False)
    language = models.CharField(max_length=200, blank=True, choices=language_choices)

    def save(self, *args, **kwargs):
        summary, highlight = utils.format_content(self.content, self.language, self.filename)
        self.content_summary = summary
        self.content_highlight = highlight

        return super(Paste, self).save(*args, **kwargs)
