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


class CSPHostnameMiddleware(object):
    """Rewrites CSP headers set by django-csp, substituting the hostname
    from the request.

    This lets you have a directive with a path without knowing the server name.

        CSP_SCRIPT_SRC = ('{host}/static/app.js',)

    N.B. This must come _before_ csp.middleware.CSPMiddleware so that it can
    process the response.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        headers = ('Content-Security-Policy', 'Content-Security-Policy-Report-Only')
        host = request.get_host()

        for header in headers:
            if header in response:
                value = response[header]
                response[header] = value.format(host=host)

        return response
