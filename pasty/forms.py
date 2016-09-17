from django import forms


class NoLabelSuffix(object):
    def __init__(self, *args, **kwargs):
        # Django overwrites label_suffix set on the class.
        kwargs.setdefault('label_suffix', u'')
        super(NoLabelSuffix, self).__init__(*args, **kwargs)


class PasteForm(NoLabelSuffix, forms.Form):
    description = forms.CharField(required=False)
    filename = forms.CharField(required=False)
    content = forms.CharField(widget=forms.Textarea)
