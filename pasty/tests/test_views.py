import datetime

import mock
from django.core.urlresolvers import reverse
from django.utils import timezone

from . import AppEngineTestCase
from ..models import Paste, Star


class PasteListTestCase(AppEngineTestCase):
    def test_shows_list_of_pastes(self):
        url = reverse('paste_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


class ApiStarTestCase(AppEngineTestCase):
    def test_star_a_paste_requires_user_login(self):
        url = reverse('api_star')

        response = self.client.post(url, {})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {u'error': u'Please sign in to star pastes'},
        )

    def test_star_a_paste_creates_star(self):
        url = reverse('api_star')
        paste = Paste.objects.create(pk='1234')
        data = {'paste': paste.pk}

        self.login('alice@example.com')
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {
                'author': 'alice@example.com',
                'id': 'alice@example.com/1234',
                'paste': '1234',
            },
        )

    def test_star_a_paste_for_non_existent_paste(self):
        url = reverse('api_star')
        data = {'paste': '1234'}

        with self.assertRaises(Paste.DoesNotExist):
            Paste.objects.get(pk='1234')

        self.login('alice@example.com')
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {'error': 'Does not exist'},
        )

    def test_star_a_paste_requires_post(self):
        url = reverse('api_star')

        self.login('alice@example.com')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)


class ApiPasteDetailTestCase(AppEngineTestCase):
    def test_error_for_non_existent_paste(self):
        url = reverse('api_paste_detail', args=('1234',))

        with self.assertRaises(Paste.DoesNotExist):
            Paste.objects.get(pk='1234')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {u'error': u'Paste does not exist'},
        )

    def test_get_paste_with_one_content_file(self):
        xmas = datetime.datetime(2016, 12, 25, tzinfo=timezone.utc)

        with mock.patch('django.utils.timezone.now', return_value=xmas):
            paste = Paste.objects.create()
            paste.save_content('foo', 'example.txt')

        url = reverse('api_paste_detail', args=(paste.pk,))

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {
                u'author': u'',
                u'created': u'2016-12-25T00:00:00Z',
                u'description': u'',
                u'filename': u'example.txt',
                u'files': [{
                    u'content': u'pasty/2016/12/25/example.txt',
                    u'created': u'2016-12-25T00:00:00Z',
                    u'filename': u'example.txt',
                    u'id': 2,
                    u'link': u'/_ah/gcs/app_default_bucket/pasty/2016/12/25/example.txt',
                }],
                u'forked_from': None,
                u'id': 1,
                u'summary': u'<table class="highlight highlight__tractable"><tr><td class="linenos"><div class="linenodiv"><pre>1</pre></div></td><td class="code"><div class="highlight highlight__trac"><pre><span></span>foo\n</pre></div>\n</td></tr></table>',
                u'tags': u'{}',
            }
        )
