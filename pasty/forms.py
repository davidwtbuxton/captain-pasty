from django import forms

from .models import Paste


class NoLabelSuffix(object):
    def __init__(self, *args, **kwargs):
        # Django overwrites label_suffix set on the class.
        kwargs.setdefault('label_suffix', u'')
        super(NoLabelSuffix, self).__init__(*args, **kwargs)


class PasteForm(NoLabelSuffix, forms.ModelForm):
    class Meta:
        model = Paste
        fields = [
            'description',
            'filename',
            'language',
            'content',
            'tags',
        ]

    def __init__(self, *args, **kwargs):
        super(PasteForm, self).__init__(*args, **kwargs)

        choices = self.fields['language'].choices
        choices[0] = (u'', u'Auto-detect language')
        choices = [(u'Language', choices)]

        self.fields['language'].choices = choices
