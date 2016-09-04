import os
import site


site.addsitedir('libs')


from djangae.wsgi import DjangaeApplication
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

application = DjangaeApplication(get_wsgi_application())
