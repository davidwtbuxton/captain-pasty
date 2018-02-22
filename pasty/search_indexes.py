from haystack import indexes

from .models import Paste


class PasteIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)

    author = indexes.CharField(model_attr='author')
    description = indexes.CharField(model_attr='description')
    created = indexes.DateTimeField(model_attr='created')

    # These 3 are for the list of files on each paste. Not sure whether I can
    # just use model_attr somehow.
    filename = indexes.MultiValueField()
    content_type = indexes.MultiValueField()
    content = indexes.MultiValueField()

    def get_model(self):
        return Paste

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_filename(self, obj):
        return [f.filename for f in obj.files]

    def prepare_content_type(self, obj):
        return [f.content_type for f in obj.files]

    def prepare_content(self, obj):
        return [f.content for f in obj.files]
