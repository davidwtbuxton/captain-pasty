import calendar
import logging
import os

from django.conf import settings
from google.appengine.api import search
from google.appengine.ext import deferred

from .models import Paste


logger = logging.getLogger(__name__)
paste_index = search.Index(name='pastes')


def datetime_to_timestamp(value):
    """Converts a datetime to a Unix timestamp."""
    return calendar.timegm(value.utctimetuple())


def add_paste(paste):
    doc = create_document_for_paste(paste)
    paste_index.put(doc)


def create_document_for_paste(paste):
    config = [
        ('author', search.TextField),
        ('description', search.TextField),
    ]

    fields = [f(name=n, value=getattr(paste, n)) for n, f in config]

    # The search API refuses to handle timezone-aware datetimes.
    created = paste.created.replace(tzinfo=None)
    fields.append(search.DateField(name='created', value=created))

    # Then we need to get the paste's content.
    for pasty_file in paste.files:
        name_field = search.TextField(name='filename', value=pasty_file.filename)
        type_field = search.TextField(name='content_type', value=pasty_file.content_type)

        with pasty_file.open('r') as fh:
            value = fh.read()
            content_field = search.TextField(name='content', value=value)

        fields.extend([name_field, type_field, content_field])

    # The default rank is just when the doc was inserted. We use the created
    # date as rank, which will automatically sort results by paste created.
    rank = datetime_to_timestamp(paste.created)
    doc_id = unicode(paste.key.id())
    doc = search.Document(doc_id=doc_id, rank=rank, fields=fields)

    return doc


class SearchResults(list):
    def __init__(self, results):
        # Guard against search docs for pastes that have been deleted.
        pastes, bad_docs = [], []

        for doc in results:
            paste = Paste.get_by_id(int(doc.doc_id))

            if paste:
                pastes.append(paste)
            else:
                bad_docs.append(doc.doc_id)

        self._results = results
        self[:] = pastes
        self.count = results.number_found

        # And schedule those search docs for deletion.
        if bad_docs:
            logger.debug('Bogus search results %r', bad_docs)
            deferred.defer(delete_docs_from_index, bad_docs, _queue='delete-docs')

    def has_next(self):
        return bool(self._results.cursor)

    def next_page_number(self):
        return self._results.cursor.web_safe_string if self.has_next() else None


def search_pastes(query, cursor_string, limit=None):
    if limit is None:
        limit = settings.PAGE_SIZE

    cursor = search.Cursor(web_safe_string=cursor_string)
    options = search.QueryOptions(cursor=cursor, ids_only=True, limit=limit)
    query = search.Query(query_string=query, options=options)

    results = paste_index.search(query)
    search_results = SearchResults(results)

    return search_results


def build_query(qdict):
    """Returns a list of (term, label) pairs from search params."""
    terms = []

    # Maps query parameters to a function which returns a pair of (term, label).
    params = {
        'author': lambda x: (u'author:"%s"' % x, u'by %s' % x),
        'content_type': lambda x: (u'content_type:"%s"' % x, u'content type like "%s"' % x),
        'filename': lambda x: (u'filename:"%s"' % x, u'filename like "%s"' % x),
        'q': lambda x: (x, u'matching "%s"' % x),
    }

    for name in params:
        value = qdict.get(name)

        if value:
            term, label = params[name](value)
            terms.append((term, label))

    return terms


def delete_docs_from_index(doc_ids):
    """Delete documents from the search index. doc_ids is a list of strings."""
    logger.debug('delete_docs_from_index(%r)', doc_ids)

    try:
        paste_index.delete(doc_ids)
    except (search.DeleteError, ValueError):
        logger.exception('Error deleting stale search results.')


def index_directory(path):
    try:
        import faker
    except ImportError:
        get_email = lambda: u'jeff@example.com'
    else:
        fake = faker.Faker()
        get_email = fake.email

    interesting = {'.py', '.html', '.js', '.txt', '.md', '.sh', '.yaml', '.css'}

    for root, dirs, files in os.walk(path):
        files = [f for f in files if os.path.splitext(f)[1].lower() in interesting]

        for f in files:
            filename = os.path.join(root, f)
            size = os.path.getsize(filename)
            print f, 'size', (size / 1024)
            if (size == 0) or (size > (1024 * 32)):
                continue

            with open(filename) as fh:
                try:
                    content = fh.read()
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    pass
                else:
                    author = get_email()
                    paste = Paste(filename=f, author=author, description=filename)
                    paste.put()
                    paste.save_content(content, filename=f)
                    add_paste(paste)
