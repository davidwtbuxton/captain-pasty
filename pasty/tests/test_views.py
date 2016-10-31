import datetime
import json

from django.core.urlresolvers import reverse

from . import AppEngineTestCase, freeze_time
from pasty.models import Paste
from pasty import utils


class PasteListTestCase(AppEngineTestCase):
    def test_shows_list_of_pastes(self):
        url = reverse('paste_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


class PasteRedirectTestCase(AppEngineTestCase):
    def test_redirects_peelings_link(self):
        paste_code = utils.base62.encode(123456789)
        url = reverse('paste_redirect', args=[paste_code])

        self.assertEqual(url, '/p/8M0kX/')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/123456789/')


class PasteRawTestCase(AppEngineTestCase):
    def test_serves_raw_file(self):
        paste = Paste()
        paste.put()
        paste.save_content('example', filename='image.jpg')

        url = reverse('paste_raw', args=[paste.key.id(), 'image.jpg'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'image/jpeg')

    def test_returns_404_for_bogus_filename(self):
        paste = Paste()
        paste.put()
        paste.save_content('example', filename='image.jpg')

        url = reverse('paste_raw', args=[paste.key.id(), 'bogus.jpg'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


class ApiStarTestCase(AppEngineTestCase):
    def test_star_a_paste_requires_user_login(self):
        url = reverse('api_star_create')

        response = self.client.post(url, {})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {u'error': u'Please sign in to star pastes'},
        )

    def test_star_a_paste_creates_star(self):
        url = reverse('api_star_create')
        paste = Paste(id=1234)
        paste.put()
        data = {'paste': paste.key.id()}

        self.login('alice@example.com')
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            sorted(response.json()),
            ['author', 'id', 'paste', 'stars']
        )

    def test_star_a_paste_for_non_existent_paste(self):
        url = reverse('api_star_create')
        data = {'paste': '1234'}

        self.assertIsNone(Paste.get_by_id(1234))

        self.login('alice@example.com')
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {'error': 'Does not exist'},
        )

    def test_star_a_paste_requires_post(self):
        url = reverse('api_star_create')

        self.login('alice@example.com')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)


class ApiPasteDetailTestCase(AppEngineTestCase):
    def test_error_for_non_existent_paste(self):
        url = reverse('api_paste_detail', args=('1234',))

        self.assertIsNone(Paste.get_by_id(1234))

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {u'error': u'Paste does not exist'},
        )

    def test_get_paste_with_one_content_file(self):
        xmas = datetime.datetime(2016, 12, 25)

        with freeze_time('2016-12-25'):
            paste = Paste(id=1234, created=xmas)
            paste.put()
            paste.save_content('foo', 'example.txt')

        url = reverse('api_paste_detail', args=(paste.key.id(),))


        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {
                u'author': None,
                u'created': u'2016-12-25T00:00:00',
                u'description': None,
                u'filename': u'example.txt',
                u'files': [{
                    u'content_type': u'text/plain',
                    u'created': u'2016-12-25T00:00:00',
                    u'filename': u'example.txt',
                    u'num_lines': 1,
                    u'path': u'pasty/2016/12/25/1234/example.txt',
                }],
                u'forked_from': None,
                u'num_files': 1,
                u'num_lines': 1,
                u'preview': u'<div class="highlight highlight__autumn"><pre><span></span>foo\n</pre></div>\n',
            }
        )


class ApiRootTestCase(AppEngineTestCase):
    def test_redirects_to_api_info(self):
        url = reverse('api_root')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/api/v1/')


class ApiPasteCreateTestCase(AppEngineTestCase):
    def test_anonymous_user_returns_error(self):
        url = reverse('api_paste_list')
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {'error': 'Please sign in to create pastes'},
        )

    def test_malformed_data_returns_error(self):
        url = reverse('api_paste_list')
        data = 'invalid'
        self.login('alice@example.com')
        response = self.client.post(url, data, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {'error': 'Invalid request'},
        )

    def test_invalid_data_returns_error(self):
        url = reverse('api_paste_list')
        self.login('alice@example.com')

        # Missing the 'content' key.
        data = {
            'description': 'Short description',
            'files': [
                {
                    'filename': 'example.txt',
                },
            ],
        }
        data = json.dumps(data)

        response = self.client.post(url, data, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {'error': "'content' is a required property"},
        )

    def test_valid_data_creates_paste(self):
        url = reverse('api_paste_list')
        self.login('alice@example.com')

        data = {
            'description': 'Short description',
            'files': [
                {
                    'filename': 'example.txt',
                    'content': 'Foo bar baz',
                },
            ],
        }
        data = json.dumps(data)

        with freeze_time('2016-12-25'):
            response = self.client.post(url, data, content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {
                u'author': u'alice@example.com',
                u'created': u'2016-12-25T00:00:00',
                u'description': u'Short description',
                u'filename': u'example.txt',
                u'files': [{
                    u'content_type': u'text/plain',
                    u'created': u'2016-12-25T00:00:00',
                    u'filename': u'example.txt',
                    u'num_lines': 1,
                    u'path': u'pasty/2016/12/25/1/example.txt',
                }],
                u'forked_from': None,
                u'num_lines': 1,
                u'num_files': 1,
                u'preview': (u'<div class="highlight highlight__autumn">'
                    '<pre><span></span>Foo bar baz\n</pre></div>\n'),
            },
        )
