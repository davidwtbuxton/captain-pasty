from google.appengine.api import users

from . import utils
from . import models


def pasty(request):
    path = request.get_full_path()
    style_options = sorted((name, value) for name, (value, _) in utils.highlight_css.items())

    return {
        'starred_pastes': models.get_starred_pastes(request.user_email),
        'login_url': users.create_login_url(path),
        'logout_url': users.create_logout_url(path),
        'highlight_styles': style_options,
        'is_current_user_admin': users.is_current_user_admin(),
    }
