import mapreduce.base_handler
import mapreduce.control
import mapreduce.mapper_pipeline
from google.appengine.ext import ndb

from . import index
from .models import Paste


_mapreduce_base_path = '/_ah/mapreduce'
_pipeline_base_path = _mapreduce_base_path + '/pipeline'


class Pipeline(mapreduce.mapper_pipeline.MapperPipeline):
    def run(self,
            job_name,
            handler_spec,
            input_reader_spec,
            output_writer_spec=None,
            params=None,
            shards=None):

        # Copied from Djangae's mapper. All this is necessary so that we can
        # point tasks at Djangae's mapreduce / pipeline handlers (base_path).

        mapreduce_id = mapreduce.control.start_map(
            job_name,
            handler_spec,
            input_reader_spec,
            params or {},
            mapreduce_parameters={
                "done_callback": self.get_callback_url(),
                "done_callback_method": "GET",
                "pipeline_id": self.pipeline_id,
                'base_path': _mapreduce_base_path
            },
            shard_count=shards,
            output_writer_spec=output_writer_spec,
            queue_name=self.queue_name,
        )
        self.fill(self.outputs.job_id, mapreduce_id)
        self.set_status(console_url="%s/detail?mapreduce_id=%s" % (
            (_mapreduce_base_path, mapreduce_id)))


def resave_pastes_task():
    pipe = Pipeline(
            'Re-save pastes.',
            handler_spec='pasty.tasks.resave_paste',
            input_reader_spec='mapreduce.input_readers.DatastoreInputReader',
            params={'entity_kind': 'pasty.models.Paste'},
            shards=4,
    )
    pipe.start(queue_name='resave-pastes', base_path=_pipeline_base_path)

    return pipe


def resave_paste(paste):
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
    pipe = Pipeline(
        'Convert peelings to pastes.',
        handler_spec='pasty.tasks.convert_peeling',
        input_reader_spec='mapreduce.input_readers.DatastoreInputReader',
        params={'entity_kind': 'pasty.models.Peeling'},
        shards=4,
    )
    pipe.start(queue_name='convert-peelings', base_path=_pipeline_base_path)

    return pipe


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


def convert_peeling(peeling):
    """Convert the previous peelings entities to pastes."""
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
