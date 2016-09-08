from google.appengine.api import users


def pasty(request):
    path = request.get_full_path()

    return {
        'login_url': users.create_login_url(path),
        'logout_url': users.create_logout_url(path),
    }
