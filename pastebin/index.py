import os

from google.appengine.api import search

from .models import Paste


paste_index = search.Index(name='pastes')


def add_paste(paste):
    doc = create_document_for_paste(paste)
    paste_index.put(doc)


def create_document_for_paste(paste):
    config = [
        ('author', search.TextField),
        ('content', search.TextField),
        ('description', search.TextField),
        ('filename', search.TextField),
        ('language', search.AtomField),
    ]

    fields = [f(name=n, value=getattr(paste, n)) for n, f in config]

    # The search API refuses to handle timezone-aware datetimes.
    created = paste.created.replace(tzinfo=None)
    fields.append(search.DateField(name='created', value=created))

    # Tags is a set field.
    tag_fields = [search.TextField(name='tags', value=value) for value in paste.tags]
    fields.extend(tag_fields)

    doc = search.Document(doc_id=unicode(paste.pk), fields=fields)

    return doc


def search_pastes(query, cursor_string):
    cursor = search.Cursor(web_safe_string=cursor_string)
    options = search.QueryOptions(cursor=cursor, ids_only=True)
    query = search.Query(query_string=query, options=options)

    results = paste_index.search(query)
    pks = [int(doc.doc_id) for doc in results]
    print 'found pks %r' % pks
    pastes = Paste.objects.filter(pk__in=pks)
    pastes.has_next = bool(results.cursor)

    pastes.next_page_number = results.cursor.web_safe_string if pastes.has_next else None

    return pastes


def index_directory(path):
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
                    paste = Paste.objects.create(filename=f, description=filename, content=content)
                    add_paste(paste)
