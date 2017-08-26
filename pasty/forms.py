from django import forms

from . import tasks


class NoLabelSuffix(object):
    def __init__(self, *args, **kwargs):
        # Django overwrites label_suffix set on the class.
        kwargs.setdefault('label_suffix', u'')
        super(NoLabelSuffix, self).__init__(*args, **kwargs)


class PasteForm(NoLabelSuffix, forms.Form):
    description = forms.CharField(required=False)
    filename = forms.CharField(required=False)
    content = forms.CharField(widget=forms.Textarea)


class SearchForm(NoLabelSuffix, forms.Form):
    q = forms.CharField(required=False)
    author = forms.CharField(required=False)
    filename = forms.CharField(required=False)
    content_type = forms.CharField(required=False)


class AdminForm(NoLabelSuffix, forms.Form):
    _tasks = [
        # (form label, task func)
        (u'Convert peelings to pastes', tasks.convert_peelings_task),
        (u'Re-save pastes', tasks.resave_pastes_task),
    ]
    _tasks = [(str(idx), label, func) for idx, (label, func) in enumerate(_tasks, 1)]

    _task_choices = [(value, label) for value, label, task in _tasks]

    tasks = forms.MultipleChoiceField(choices=_task_choices, widget=forms.CheckboxSelectMultiple)

    def clean_tasks(self):
        chosen = self.cleaned_data['tasks']

        return [(label, task) for value, label, task in self._tasks if value in chosen]
