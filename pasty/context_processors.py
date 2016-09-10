from google.appengine.api import users

from .models import get_starred_pastes


def pasty(request):
    path = request.get_full_path()

    return {
        'starred_pastes': get_starred_pastes(request.user_email),
        'login_url': users.create_login_url(path),
        'logout_url': users.create_logout_url(path),
    }
