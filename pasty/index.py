import calendar
import os

from google.appengine.api import search

from .models import Paste


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
        ('filename', search.TextField),
    ]

    fields = [f(name=n, value=getattr(paste, n)) for n, f in config]

    # The search API refuses to handle timezone-aware datetimes.
    created = paste.created.replace(tzinfo=None)
    fields.append(search.DateField(name='created', value=created))

    # Then we need to get the paste's content.
    contents = []

    for pasty_file in paste.files.all():
        pasty_file.content.seek(0)
        value = pasty_file.content.read()
        contents.append(value)

    fields.append(search.TextField(name='content', value='\n\n'.join(contents)))

    # The default rank is just when the doc was inserted. We use the created
    # date as rank, which will automatically sort results by paste created.
    rank = datetime_to_timestamp(paste.created)

    doc = search.Document(doc_id=unicode(paste.pk), rank=rank, fields=fields)

    return doc


def search_pastes(query, cursor_string):
    cursor = search.Cursor(web_safe_string=cursor_string)
    options = search.QueryOptions(cursor=cursor, ids_only=True)
    query = search.Query(query_string=query, options=options)

    results = paste_index.search(query)
    pks = [int(doc.doc_id) for doc in results]
    pastes = Paste.objects.filter(pk__in=pks)
    pastes.has_next = bool(results.cursor)

    pastes.next_page_number = results.cursor.web_safe_string if pastes.has_next else None

    return pastes


def build_query(qdict):
    """Returns a list of (term, label) pairs from search params.

    Combine the term parts to search for all parameters.
    """
    terms = []

    author = qdict.get('author')
    if author:
        term = u'author:"%s"' % author
        label = u'by %s' % author
        terms.append((term, label))

    q = qdict.get('q')
    if q:
        label = u'containing "%s"' % q
        terms.append((q, label))

    return terms


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
                    paste = Paste.objects.create(filename=f, author=author, description=filename)
                    paste.save_content(content, filename=f)
                    add_paste(paste)
