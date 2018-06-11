import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote

from . import index


PasteListQuery = endpoints.ResourceContainer(
    message_types.VoidMessage,
    author = messages.StringField(1),
    content_type = messages.StringField(2),
    filename = messages.StringField(3),
    q = messages.StringField(4),
    p = messages.StringField(5),
)


class PastyFileMessage(messages.Message):
    created = message_types.DateTimeField(1)
    filename = messages.StringField(2)
    content_type = messages.StringField(3)
    num_lines = messages.IntegerField(4)
    path = messages.StringField(5)
    relative_path = messages.StringField(6)


class PasteMessage(messages.Message):
    created = message_types.DateTimeField(1)
    author = messages.StringField(2)
    filename = messages.StringField(3)
    description = messages.StringField(4)
    fork = messages.StringField(5)
    files = messages.MessageField(PastyFileMessage, 6, repeated=True)
    preview = messages.StringField(7)


class PasteListMessage(messages.Message):
    pastes = messages.MessageField(PasteMessage, 1, repeated=True)
    next = messages.StringField(2)


@endpoints.api('pasty', '1.0', base_path='/api/')
class PastyAPI(remote.Service):

    @endpoints.method(PasteListQuery, PasteListMessage, http_method='GET')
    def paste_list(self, request):
        page = request.p
        terms = index.build_query(request.GET)
        query = u' '.join(term for term, label, param in terms).encode('utf-8')
        pastes = index.search_pastes(query, page)

        if pastes.has_next():
            next_page = '%s?p=%s' % (request.path, pastes.next_page_number())
            next_page = request.build_absolute_uri(next_page)
        else:
            next_page = None

        paste_list = [PasteMessage(**p.to_dict()) for p in pastes]
        response = PasteListMessage(next=next_page, pastes=paste_list)

        return response


# The WSGI handler. This is mapped in app.yaml.
app = endpoints.api_server([PastyAPI])
