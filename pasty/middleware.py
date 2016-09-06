from . import utils


class GoogleUserMiddleware(object):
    """Sets a user_email attribute on the request object, which is the
    currently logged in Google Auth user email (if any).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        email = utils.get_current_user_email()
        request.user_email = email

        response = self.get_response(request)

        return response
