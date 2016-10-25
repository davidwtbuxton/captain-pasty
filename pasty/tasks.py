import mapreduce.mapreduce_pipeline
import pipeline

from . import index


class PastePipeline(pipeline.Pipeline):
    def run(self, *args, **kwargs):
        yield mapreduce.mapreduce_pipeline.MapperPipeline(
            'Re-save pastes.',
            handler_spec='pasty.tasks.save_paste',
            input_reader_spec='mapreduce.input_readers.DatastoreInputReader',
            params={'entity_kind': 'pasty.models.Paste'},
            shards=1,
        )


def resave_pastes():
    pipe = PastePipeline()
    pipe.start(queue_name='resave-pastes')

    return pipe


def save_paste(paste):
    dirty = False

    if not paste.filename:
        dirty = True
        paste.filename = u''

    if not paste.description:
        dirty = True
        paste.description = u''

    if dirty:
        paste.save()

    index.add_paste(paste)
