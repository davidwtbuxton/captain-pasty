import mapreduce.base_handler
import mapreduce.control
import mapreduce.mapper_pipeline

from . import index


_mapreduce_base_path = '/_ah/mapreduce'
_pipeline_base_path = _mapreduce_base_path + '/pipeline'


class PastePipeline(mapreduce.mapper_pipeline.MapperPipeline):
    def run(self,
            job_name,
            handler_spec,
            input_reader_spec,
            output_writer_spec=None,
            params=None,
            shards=None):

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


def resave_pastes():
    pipe = PastePipeline(
            'Re-save pastes.',
            handler_spec='pasty.tasks.save_paste',
            input_reader_spec='mapreduce.input_readers.DatastoreInputReader',
            params={'entity_kind': 'pasty.models.Paste'},
            shards=1,
    )
    pipe.start(queue_name='resave-pastes', base_path=_pipeline_base_path)

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
        paste.put()

    index.add_paste(paste)
