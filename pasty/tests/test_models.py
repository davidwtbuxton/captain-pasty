import datetime
import unittest

from django.http import Http404

from . import AppEngineTestCase
from pasty.models import LexerConfig, Paste, PastyFile, make_relative_path


class PasteTestCase(AppEngineTestCase):
    def test_unicode(self):
        obj = Paste(author='alice@example.com', filename='example.txt')

        self.assertEqual(unicode(obj), u'alice@example.com / example.txt')

    def test_unicode_for_anonymous_author(self):
        obj = Paste(filename='example.txt')

        self.assertEqual(unicode(obj), u'anonymous / example.txt')

    def test_get_or_404_with_none_id(self):
        with self.assertRaises(Http404):
            Paste.get_or_404(None)

    def test_get_or_404_with_bad_id(self):
        with self.assertRaises(Http404):
            Paste.get_or_404('bogus')

    def test_get_or_404_with_unknown_id(self):
        self.assertIsNone(Paste.get_by_id(1234))

        with self.assertRaises(Http404):
            Paste.get_or_404(1234)

    def test_get_or_404_returns_paste_for_valid_integer_id(self):
        Paste(id=1234).put()

        obj = Paste.get_or_404(1234)

        self.assertEqual(obj.key.id(), 1234)

    def test_get_or_404_returns_paste_for_valid_string_id(self):
        Paste(id=1234).put()

        obj = Paste.get_or_404('1234')

        self.assertEqual(obj.key.id(), 1234)

    def test_to_dict_for_forked_paste(self):
        xmas = datetime.datetime(2016, 12, 25)
        orig_key = Paste(id=1234, created=xmas).put()
        fork = Paste(id=5678, created=xmas, fork=orig_key)
        fork.put()

        result = fork.to_dict()

        self.assertEqual(
            result,
            {
                u'author': None,
                u'created': xmas,
                u'description': None,
                u'filename': 'untitled.txt',
                u'files': [],
                u'fork': 1234,
                u'id': 5678,
                u'num_files': 0,
                u'num_lines': 0,
                u'preview': None,
                u'url': u'/5678/',
            },
        )

    def test_highlight_content_with_custom_lexer_config(self):
        config = LexerConfig.get()
        config.lexers = [{'extension': 'sass', 'language': 'CSS'}]
        config.put()

        # Same content, but different filenames.
        files = [
            ('example.sass', 'body { font-family: serif; }'),
            ('example.txt', 'body { font-family: serif; }'),
        ]
        paste = Paste.create_with_files(files=files)

        css_expected = (
            u'<div class="highlight highlight__autumn"><pre><span></span>'
            u'<span class="nt">body</span> <span class="p">{</span>'
            u' <span class="nb">font-family</span><span class="o">:</span>'
            u' <span class="nb">serif</span><span class="p">;</span>'
            u' <span class="p">}</span>\n</pre></div>\n'
        )
        txt_expected = (
            u'<div class="highlight highlight__autumn"><pre><span></span>'
            u'body { font-family: serif; }\n</pre></div>\n'
        )

        self.assertEqual(paste.preview, css_expected)
        # The sass file was highlighted as CSS.
        self.assertEqual(paste.files[0].content_highlight(), css_expected)
        self.assertEqual(paste.files[1].content_highlight(), txt_expected)


class PastyFileTestCase(AppEngineTestCase):
    def test_default_content_type(self):
        obj = PastyFile()

        self.assertEqual(obj.content_type, 'text/plain')

    def test_known_content_type(self):
        obj = PastyFile(filename='example.jpg')

        self.assertEqual(obj.content_type, 'image/jpeg')


class LexerConfigTestCase(AppEngineTestCase):
    def test_get_singleton(self):
        config = LexerConfig.get()

        self.assertEqual(config.lexers, [])
        self.assertEqual(config.key.id(), 'config')

    def test_adding_config(self):
        config = LexerConfig.get()

        m = LexerConfig.mapping(extension='foo', language='FooLang')
        config.lexers.append(m)
        config.put()

        config = LexerConfig.get()
        self.assertEqual(config.lexers, [m])


class MakeRelativePathTestCase(unittest.TestCase):
    def test_valid_file_path(self):
        result = make_relative_path('pasty/1999/1/1/123/1/foo.html')

        self.assertEqual(result, '1/foo.html')

    def test_invalid_file_path_error(self):
        with self.assertRaisesRegexp(ValueError, 'Invalid file path'):
            make_relative_path('pasty/1999/1/1/abc/1/foo.html')
