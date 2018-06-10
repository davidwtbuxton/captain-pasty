import io
import os.path
import string

import pygments
from google.appengine.api import users
from pygments import formatters
from pygments import lexers
from pygments import styles
from pygments.util import ClassNotFound


PYGMENTS_STYLE = 'autumn'


def get_current_user_email():
    user = users.get_current_user()

    return user.email() if user else u''


def get_language_names():
    """Returns a sorted list of the syntaxes supported for highlighting."""
    names = [name for name, aliases, ftypes, mtypes in lexers.get_all_lexers()]
    names.sort(key=lambda x: x.lower())

    return names


def choose_lexer(content, filename=None, config=None):
    """Returns a Pygments lexer.

    config is a mapping of extensions to lexer names, {'.foo': 'FooLang'}
    """
    lexer = None

    if filename:
        _, ext = os.path.splitext(filename.lower())
        no_dot_ext = ext.lstrip('.')

        if config and (no_dot_ext in config):
            try:
                lexer = lexers.get_lexer_by_name(config[no_dot_ext])
            except ClassNotFound:
                pass

        elif ext == '.txt':
            # Else we get the ResourceLexer, which is not useful.
            lexer = lexers.get_lexer_by_name('text')

        else:
            try:
                lexer = lexers.get_lexer_for_filename(filename)
            except ClassNotFound:
                pass

    if not lexer:
        try:
            lexer = lexers.guess_lexer(content)
        except ClassNotFound:
            # No match by filename, and Pygments can't guess what it is.
            # So let's treat it as plain text.
            lexer = lexers.get_lexer_by_name('text')

    return lexer


def ext_for_lexer(lexer):
    """Returns a filename extension (including a dot) for the Lexer."""
    try:
        pattern = lexer.filenames[0]
    except IndexError:
        pattern = '*.txt'

    ext = pattern.lstrip('*')

    return ext


def highlight_content(content, filename=None, config=None):
    """Chooses a lexer and applies code highlighting. If filename is None then
    the language is guessed from the content.

    Returns a pair of (lexer, content).
    """
    lexer = choose_lexer(content, filename=filename, config=config)

    style_class = highlight_css[PYGMENTS_STYLE][0]
    cssclass = 'highlight ' + style_class
    formatter = formatters.HtmlFormatter(style=PYGMENTS_STYLE, cssclass=cssclass)
    highlighted = pygments.highlight(content, lexer, formatter)

    return lexer, highlighted


def summarize_content(content, **kwargs):
    """Summarizes and adds code highlighting to text.

    Returns a pair of (lexer, summary).
    """
    lines = 10
    max_summary_size = 10 * 256
    content = content[:max_summary_size]

    summary = u'\n'.join(content.strip().splitlines()[:lines]).strip()
    lexer, summary = highlight_content(summary, **kwargs)

    return lexer, summary


def get_all_highlight_css():
    """Yields pairs of (<name>, <css-string>) for every Pygment HTML style."""
    for name in styles.get_all_styles():
        cssclass = 'highlight__' + name
        formatter = formatters.HtmlFormatter(style=name, cssclass=cssclass)
        css = formatter.get_style_defs()
        css = (u'/* Pygment\'s %s style. */\n' % name) + css

        yield (name, cssclass, css)


#: Mapping of {<style-name>: (<class-name>, <css>)}.
highlight_css = {name: (klass, style) for name, klass, style in get_all_highlight_css()}


def highlight_styles():
    """Returns the syntax highlighting CSS as an encoded string."""
    content = u'\n\n'.join(css for _, css in highlight_css.values())
    content = content.encode('utf-8')

    return content


def count_lines(content):
    """Returns the number of lines for a string."""
    try:
        fh = io.StringIO(content)
    except TypeError:
        fh = io.BytesIO(content)

    count = 0

    for count, _ in enumerate(fh, 1):
        pass

    return count


class BaseConverter(object):
    def __init__(self, digits):
        self.digits = digits
        self.base = len(digits)

    def encode(self, value):
        base, digits = self.base, self.digits

        if value < 0:
            sign = '-'
            value = abs(value)
        else:
            sign = ''

        value, rem = divmod(value, base)
        chars = [digits[rem]]

        while value:
            value, rem = divmod(value, base)
            chars.append(digits[rem])

        return sign + ''.join(reversed(chars))

    def decode(self, value):
        base, digits = self.base, self.digits

        if value.startswith('-'):
            sign = -1
            value = value[1:]
        else:
            sign = 1

        result = 0

        for power, char in enumerate(reversed(value)):
            pos = digits.index(char)
            result += (base ** power) * pos

        return result * sign


base62 = BaseConverter(string.digits + string.ascii_uppercase + string.ascii_lowercase)
