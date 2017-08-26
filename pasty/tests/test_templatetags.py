import datetime

import freezegun
from django import forms
from django.http.request import QueryDict
from django.template import Context, Template
from django.test import TestCase

from pasty.templatetags import pastytags


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


class ParamsTestCase(TestCase):
    def test_adding_new_parameter(self):
        qd = QueryDict(mutable=True)
        qd['a'] = 'b'

        result = pastytags.params(qd, foo='bar')

        self.assertEqual(result, 'a=b&foo=bar')

    def test_replacing_existing_parameter(self):
        qd = QueryDict(mutable=True)
        qd['a'] = 'b'
        qd['foo'] = 'bar'

        result = pastytags.params(qd, foo='qux')

        self.assertEqual(result, 'a=b&foo=qux')

    def test_removing_existing_parameter(self):
        qd = QueryDict(mutable=True)
        qd['a'] = 'b'
        qd['foo'] = 'bar'

        result = pastytags.params(qd, foo=None)

        self.assertEqual(result, 'a=b')


class SinceTestCase(TestCase):
    def test_date_less_than_2_days_old(self):
        new_years_eve = datetime.datetime(1999, 12, 31)

        with freezegun.freeze_time('2000-01-01'):
            result = pastytags.since(new_years_eve)

        self.assertEqual(result, '1 day ago')

    def test_less_than_a_minute_old(self):
        new_years_eve = datetime.datetime(1999, 12, 31, 23, 59, 59)

        with freezegun.freeze_time('2000-01-01'):
            result = pastytags.since(new_years_eve)

        self.assertEqual(result, '1 second ago')

    def test_less_than_an_hour_old(self):
        new_years_eve = datetime.datetime(1999, 12, 31, 23, 1)

        with freezegun.freeze_time('2000-01-01'):
            result = pastytags.since(new_years_eve)

        self.assertEqual(result, '59 minutes ago')

    def test_less_than_an_hour_old(self):
        new_years_eve = datetime.datetime(1999, 12, 31, 23, 1)

        with freezegun.freeze_time('2000-01-01'):
            result = pastytags.since(new_years_eve)

        self.assertEqual(result, '59 minutes ago')

    def test_older_than_2_days(self):
        # Anything older than 2 days gets the regular date formatting.
        xmas = datetime.datetime(1999, 12, 25)

        with freezegun.freeze_time('2000-01-01'):
            result = pastytags.since(xmas)

        self.assertEqual(result, 'Dec. 25, 1999')
