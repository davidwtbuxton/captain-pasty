import datetime
import json
import unittest

from django.core.urlresolvers import reverse

from . import AppEngineTestCase, freeze_time
from pasty.models import LexerConfig, Paste, Star, get_starred_pastes
from pasty import index
from pasty import utils


class PasteHomeTestCase(AppEngineTestCase):
    def test_redirects_to_new_page(self):
        url = reverse('home')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/new/')


class PasteListTestCase(AppEngineTestCase):
    def test_shows_list_of_pastes(self):
        for n in range(11):
            paste = Paste()
            paste.put()
            paste.save_content('foo %s' % n, filename='example-%s.txt' % n)
            index.add_paste(paste)

        url = reverse('paste_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, 'pasty/paste_list.html')
        self.assertEqual(
            sorted(response.context_data),
            ['page_title', 'pastes', 'section', 'terms'],
        )
        self.assertEqual(response.context_data['pastes'].count, 11)


class PasteDetailTestCase(AppEngineTestCase):
    def test_shows_detail_for_paste(self):
        paste = Paste(id=1234, filename='example.txt')
        paste.put()
        paste.save_content('foo', filename='example.txt')

        url = reverse('paste_detail', args=[paste.key.id()])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context_data,
            {
                'page_title': 'example.txt',
                'paste': paste,
                'starred': None,
            },
        )

    def test_shows_detail_for_paste_without_filename_or_description(self):
        paste = Paste(id=1234, filename='')
        paste.put()
        paste.save_content('foo bar baz', filename='')

        url = reverse('paste_detail', args=[paste.key.id()])
        response = self.client.get(url)

        self.assertContains(response, 'foo bar baz', status_code=200)

class PasteRedirectTestCase(AppEngineTestCase):
    def test_redirects_peelings_link(self):
        paste_code = utils.base62.encode(123456789)
        url = reverse('paste_redirect', args=[paste_code])

        self.assertEqual(url, '/p/8M0kX/')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/123456789/')


class PasteDownloadTestCase(AppEngineTestCase):
    def test_download_paste_files_as_zip(self):
        paste = Paste(id=1234)
        paste.put()
        paste.save_content('foo', filename='example.txt')

        url = reverse('paste_download', args=[paste.key.id()])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="example.txt.zip"')
        self.assertEqual(response['Content-type'], 'application/zip')


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


class PasteCreateTestCase(AppEngineTestCase):
    def test_shows_empty_form_on_get(self):
        url = reverse('paste_create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sorted(response.context_data),
            ['form', 'page_title', 'section'],
        )
        self.assertEqual(response.context_data['page_title'], u'New paste')
        self.assertEqual(response.context_data['section'], 'paste_create')

    def test_forking_from_paste_pre_fills_form(self):
        paste = Paste(id=1234, description='Foo')
        paste.put()
        paste.save_content('foo bar baz', filename='example.txt')

        url = reverse('paste_create')
        response = self.client.get(url, {'fork': paste.key.id()})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sorted(response.context_data),
            ['form', 'page_title', 'section'],
        )
        self.assertEqual(response.context_data['page_title'], u'New paste')
        self.assertEqual(response.context_data['section'], 'paste_create')
        self.assertEqual(
            response.context_data['form'].initial,
            {
                'content': 'foo bar baz',
                'description': 'Foo',
                'filename': 'example.txt',
            },
        )

    def test_create_a_new_paste_on_post(self):
        self.assertIsNone(Paste.get_by_id(1))

        data = {
            'description': 'Foo',
            'filename': 'example.txt',
            'content': 'foo bar baz',
        }

        url = reverse('paste_create')
        with freeze_time('2016-12-25'):
            response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/1/')

        paste = Paste.get_by_id(1)

        self.assertEqual(
            paste.to_dict(),
            {
                'author': u'',
                'created': datetime.datetime(2016, 12, 25),
                'description': 'Foo',
                'filename': 'example.txt',
                'files': [
                    {
                        'content_type': 'text/plain',
                        'created': datetime.datetime(2016, 12, 25),
                        'filename': 'example.txt',
                        'num_lines': 1,
                        'path': 'pasty/2016/12/25/1/1-example.txt',
                    },
                ],
                'forked_from': None,
                'id': 1,
                'num_files': 1,
                'num_lines': 1,
                'preview': (
                    '<div class="highlight highlight__autumn">'
                    '<pre><span></span>foo bar baz\n</pre></div>\n'
                ),
                'url': '/1/',
            },
        )

    def test_create_a_new_paste_without_filename_or_description(self):
        self.assertIsNone(Paste.get_by_id(1))

        data = {
            'filename': '',
            'description': '',
            'content': 'foo bar baz',
        }
        url = reverse('paste_create')

        with freeze_time('2016-12-25'):
            response = self.client.post(url, data)

        detail_url = reverse('paste_detail', args=[1])

        self.assertRedirects(response, detail_url)

        paste = Paste.get_by_id(1)

        self.assertEqual(
            paste.to_dict(),
            {
                'author': u'',
                'created': datetime.datetime(2016, 12, 25),
                'description': u'',
                'filename': u'untitled.txt',
                'files': [
                    {
                        'content_type': 'text/plain',
                        'created': datetime.datetime(2016, 12, 25),
                        'filename': 'untitled.txt',
                        'num_lines': 1,
                        'path': u'pasty/2016/12/25/1/1-untitled.txt',
                    },
                ],
                'forked_from': None,
                'id': 1,
                'num_files': 1,
                'num_lines': 1,
                'preview': (
                    '<div class="highlight highlight__autumn">'
                    '<pre><span></span>foo bar baz\n</pre></div>\n'
                ),
                'url': '/1/',
            },
        )

    def test_create_new_paste_with_duplicate_filenames(self):
        self.assertIsNone(Paste.get_by_id(1))

        data = {
            'description': 'Foo',
            'filename': ['example.txt', 'example.txt'],
            'content': ['foo', 'bar'],
        }

        url = reverse('paste_create')
        with freeze_time('2016-12-25'):
            response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/1/')

        paste = Paste.get_by_id(1)

        self.assertEqual(
            paste.to_dict(),
            {
                'author': u'',
                'created': datetime.datetime(2016, 12, 25),
                'description': 'Foo',
                'filename': 'example.txt',
                'files': [
                    {
                        'content_type': 'text/plain',
                        'created': datetime.datetime(2016, 12, 25),
                        'filename': 'example.txt',
                        'num_lines': 1,
                        'path': 'pasty/2016/12/25/1/1-example.txt',
                    },
                    {
                        'content_type': 'text/plain',
                        'created': datetime.datetime(2016, 12, 25),
                        'filename': 'example.txt',
                        'num_lines': 1,
                        'path': 'pasty/2016/12/25/1/2-example.txt',
                    },
                ],
                'forked_from': None,
                'id': 1,
                'num_files': 2,
                'num_lines': 2,
                'preview': (
                    '<div class="highlight highlight__autumn">'
                    '<pre><span></span>foo\n</pre></div>\n'
                ),
                'url': '/1/',
            },
        )


class ApiStarListTestCase(AppEngineTestCase):
    def test_anonymous_user_denied(self):
        url = reverse('api_star_list')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {u'error': u'Please sign in to star pastes'},
        )

    def test_shows_empty_list_of_stars(self):
        url = reverse('api_star_list')

        self.login('alice@example.com')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {u'stars': []},
        )

    def test_shows_starred_pastes(self):
        user_email = u'alice@example.com'

        paste = Paste(id=1234, created=datetime.datetime(2016, 12, 25))
        paste.put()
        starred = paste.create_star_for_author(user_email)

        url = reverse('api_star_list')

        self.login(user_email)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {
                u'stars': [
                    {
                        u'author': None,
                        u'created': u'2016-12-25T00:00:00',
                        u'description': None,
                        u'filename': 'untitled.txt',
                        u'files': [],
                        u'forked_from': None,
                        u'id': 1234,
                        u'num_files': 0,
                        u'num_lines': 0,
                        u'preview': None,
                        u'url': u'/1234/',
                    },
                ],
            },
        )


class ApiStarCreateTestCase(AppEngineTestCase):
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
            ['author', 'id', 'paste', 'stars'],
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


class ApiStarDeleteTestCase(AppEngineTestCase):
    def test_unstar_requires_login(self):
        url = reverse('api_star_delete')

        response = self.client.post(url, {})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {u'error': u'Please sign in to star pastes'},
        )

    def test_unstar_non_existent_paste(self):
        url = reverse('api_star_delete')
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

    def test_unstar_a_paste_removes_star(self):
        user_email = 'alice@example.com'
        self.login(user_email)

        paste = Paste(id=1234)
        paste.put()
        starred = paste.create_star_for_author(user_email)

        self.assertEqual(get_starred_pastes(user_email), [paste])

        data = {'paste': paste.key.id()}

        url = reverse('api_star_delete')
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(
            response.json(),
            {
                'id': starred.key.id(),
                'stars': [],
            }
        )


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
                    u'path': u'pasty/2016/12/25/1234/1-example.txt',
                }],
                u'forked_from': None,
                u'id': 1234,
                u'num_files': 1,
                u'num_lines': 1,
                u'preview': u'<div class="highlight highlight__autumn"><pre><span></span>foo\n</pre></div>\n',
                u'url': u'/1234/',
            }
        )


class ApiRootTestCase(AppEngineTestCase):
    def test_redirects_to_api_info(self):
        url = reverse('api_root')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/api/v1/')


class ApiIndexTestCase(AppEngineTestCase):
    @unittest.expectedFailure
    def test_returns_list_of_api_routes(self):
        url = reverse('api_index')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})


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
                    u'path': u'pasty/2016/12/25/1/1-example.txt',
                }],
                u'forked_from': None,
                u'id': 1,
                u'num_lines': 1,
                u'num_files': 1,
                u'preview': (u'<div class="highlight highlight__autumn">'
                    '<pre><span></span>Foo bar baz\n</pre></div>\n'),
                u'url': u'/1/',
            },
        )


class AdminLexersTestCase(AppEngineTestCase):
    def test_shows_form(self):
        url = reverse('admin_lexers')
        self.login('alice@example.com', is_admin=True)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_add_new_lexer_mapping(self):
        url = reverse('admin_lexers')
        self.login('alice@example.com', is_admin=True)

        self.assertEqual(LexerConfig.get_config(), {})

        data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-language': 'AppleScript',
            'form-0-extension': 'script',
        }

        response = self.client.post(url, data)

        self.assertRedirects(response, url)
        self.assertEqual(LexerConfig.get_config(), {'script': 'AppleScript'})
