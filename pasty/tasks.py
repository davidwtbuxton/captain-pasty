import datetime

from djangae.db.migrations import mapper_library
from google.appengine.api import datastore
from google.appengine.ext import ndb

from . import index
from .models import Paste


def entity_to_instance(entity):
    """Returns an ndb model instance for the datastore entity."""
    key_path = entity.key().to_path()
    key = ndb.Key(flat=key_path)
    obj = key.get()

    return obj


def resave_pastes_task():
    dt = datetime.datetime.utcnow()
    name = 'resave-pastes {}'.format(dt)
    q = 'resave-pastes'
    query = datastore.Query('Paste')
    mapper_library.start_mapping(name, query, resave_paste, queue=q)


def resave_paste(entity):
    paste = entity_to_instance(entity)
    dirty = False

    if not paste.filename:
        dirty = True
        paste.filename = u''

    if not paste.description:
        dirty = True
        paste.description = u''

    if dirty:
        paste.put()

    index.add_paste(paste)


def convert_peelings_task():
    dt = datetime.datetime.utcnow()
    name = 'convert-peelings {}'.format(dt)
    q = 'convert-peelings'
    query = datastore.Query('Peeling')
    mapper_library.start_mapping(name, query, convert_peeling, queue=q)


def make_peeling_filename(obj):
    # Peelings have a language, but no filename.
    language_map = {
        'JSCRIPT': '.js',
        'PLAIN': '.txt',
        'BASH': '.sh',
        'PYTHON': '.py',
        'CSS': '.css',
        'SQL': '.sql',
        'CPP': '.cpp',
        'DIFF': '.diff',
        'POWERSHELL': '.ps1',
    }

    language = obj['language']

    return u'untitled' + language_map.get(language, '.txt')


def convert_peeling(entity):
    """Convert the previous peelings entities to pastes."""
    peeling = entity_to_instance(entity)
    data = peeling.to_dict()
    paste_id = peeling.key.id()
    forked_from = ndb.Key(Paste, data['fork_of_id']) if data['fork_of_id'] else None
    filename = make_peeling_filename(data)

    obj = Paste(
        id=paste_id,
        author=None, # All peelings were anonymous.
        created=data['created'],
        filename='',
        description=data['title'],
        forked_from=forked_from,
    )
    obj.put()
    obj.save_content(data['content'], filename=filename)
