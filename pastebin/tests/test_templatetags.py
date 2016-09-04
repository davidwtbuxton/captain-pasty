from django import forms
from django.template import Context, Template
from django.test import TestCase


class TestForm(forms.Form):
    error_css_class = 'error'
    required_css_class = 'required'

    name = forms.CharField()


class ReformTestCase(TestCase):
    def test_render_input_adds_classes(self):
        template = Template('''{% render_input form.name class="foo" %}''')
        context = Context({'form': TestForm()})

        result = template.render(context)
        expected = u'<input class="foo" id="id_name" name="name" type="text" required />'

        self.assertEqual(result, expected)

    def test_render_label_adds_classes(self):
        template = Template('''{% render_label form.name class="foo" %}''')
        context = Context({'form': TestForm()})

        result = template.render(context)
        expected = u'<label class="foo required" for="id_name">Name:</label>'

        self.assertEqual(result, expected)
