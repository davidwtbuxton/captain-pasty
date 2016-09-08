import pygments
from google.appengine.api import users
from pygments import formatters
from pygments import lexers
from pygments import styles
from pygments.util import ClassNotFound


PYGMENTS_STYLE = 'trac'


def get_current_user_email():
    user = users.get_current_user()

    return user.email() if user else u''


def get_language_names():
    """Returns a sorted list of the syntaxes supported for highlighting."""
    names = [name for name, aliases, ftypes, mtypes in lexers.get_all_lexers()]
    names.sort(key=lambda x: x.lower())

    return names


def highlight_content(content, language=None, filename=None):
    """Applies code highlighting and returns the markup. If language or filename
    is None then the language is guessed from the content.
    """
    lexer = None

    if language:
        try:
            lexer = lexers.get_lexer_by_name(language)
        except ClassNotFound:
            pass

    if filename:
        try:
            lexer = lexers.get_lexer_for_filename(filename)
        except ClassNotFound:
            pass

    if not lexer:
        try:
            lexer = lexers.guess_lexer(content)
        except ClassNotFound:
            # No match by language or filename, and Pygments can't guess what
            # it is. So let's treat it as plain text.
            lexer = lexers.get_lexer_by_name('text')

    style = PYGMENTS_STYLE
    cssclass = 'highlight highlight__' + style
    formatter = formatters.HtmlFormatter(style=style, cssclass=cssclass, linenos='table')
    highlighted = pygments.highlight(content, lexer, formatter)

    return highlighted


def summarize_content(content, language=None, filename=None):
    """Returns a summary of the content, with syntax highlighting."""
    lines = 10
    summary = u'\n'.join(content.strip().splitlines()[:lines]).strip()
    summary = highlight_content(summary, language=language)

    return summary


def get_all_highlight_css():
    """Yields pairs of (<name>, <css-string>) for every Pygment HTML style."""
    for name in styles.get_all_styles():
        cssclass = 'highlight__' + name
        formatter = formatters.HtmlFormatter(style=name, cssclass=cssclass)
        css = formatter.get_style_defs()
        css = (u'/* Pygment\'s %s style. */\n' % name) + css

        yield (name, css)


#: Mapping of {<style-name>: <css>}.
highlight_css = dict(get_all_highlight_css())


def get_url_patterns(prefix=None):
    """Returns a list of url definitions, optionally filtered by patterns
    matching the prefix.

    Each item is a pair of (name, pattern).
    """
    return []
