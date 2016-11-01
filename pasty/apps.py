from django.apps import AppConfig

from . import content_types


class PastyAppConfig(AppConfig):
    name = 'pasty'

    def ready(self):
        content_types.add_content_types()
