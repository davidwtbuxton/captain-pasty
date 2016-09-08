from django import forms

from .models import Paste


class NoLabelSuffix(object):
    def __init__(self, *args, **kwargs):
        # Django overwrites label_suffix set on the class.
        kwargs.setdefault('label_suffix', u'')
        super(NoLabelSuffix, self).__init__(*args, **kwargs)


class PasteForm(NoLabelSuffix, forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Paste
        fields = [
            'description',
            'filename',
        ]
