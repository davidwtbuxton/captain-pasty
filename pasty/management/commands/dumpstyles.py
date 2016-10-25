from django.core.management.base import BaseCommand

from pasty import utils


class Command(BaseCommand):
    help = 'Output the CSS for syntax highlighting'

    def handle(self, *args, **options):
        text = utils.highlight_styles()
        self.stdout.write(text)
