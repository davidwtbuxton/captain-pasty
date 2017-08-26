from . import AppEngineTestCase
from pasty.forms import AdminLexersFormSet
from pasty.models import LexerConfig


class AdminLexersFormSetTestCase(AppEngineTestCase):
    def test_initial_formset_for_config(self):
        config = LexerConfig.get()
        config.lexers = [
            LexerConfig.mapping(extension='foo', language='FooLang'),
            LexerConfig.mapping(extension='bar', language='BarLang'),
        ]
        config.put()

        formset = AdminLexersFormSet.for_config()

        self.assertEqual(
            formset.initial,
            [
                {'extension': u'bar', 'language': u'BarLang'},
                {'extension': u'foo', 'language': u'FooLang'},
            ],
        )
