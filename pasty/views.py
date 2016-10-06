import json
import zipfile

import jsonschema
import mistune
from djangae.contrib.pagination import Paginator
from django.conf import settings
from django.core.paginator import InvalidPage
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse as render
from django.utils import safestring
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import index
from . import utils
from .forms import PasteForm
from .models import Paste, Star


def home(request):
    return redirect('paste_create')


def paste_list(request):
    """Shows recent pastes."""
    per_page = settings.PAGE_SIZE
    pastes = Paste.query().order(-Paste.created).fetch(per_page)

    context = {
        'page_title': u'Pastes',
        'pastes': pastes,
        'section': 'paste_list',
    }

    return render(request, 'paste_list.html', context)


def paste_search(request):
    """Shows a synopsis of pastes.

    You can search for pastes by author and tag, or search the paste content.

    /?author=jeff@example.com - finds pastes by jeff@example.com
    /?tag=python&tag=javascript - finds pasted tagged 'python' OR 'javascript'
    /?q=foo - finds pastes containing the word 'foo'
    """
    query = request.GET.get('q')
    page = request.GET.get('p')

    terms = index.build_query(request.GET)
    query = u' '.join(term for term, label in terms).encode('utf-8')
    pastes = index.search_pastes(query, page) if query else []

    context = {
        'page_title': u'Pastes',
        'pastes': pastes,
        'section': 'paste_search',
        'tags': [label for term, label in terms],
    }

    return render(request, 'paste_list.html', context)


def paste_detail(request, paste_id):
    paste = Paste.get_by_id(int(paste_id))
    if not paste:
        raise Http404

    starred = Star.query(Star.author==request.user_email, Star.paste==paste.key).get()

    context = {
        'page_title': paste.filename,
        'paste': paste,
        'starred': starred,
    }

    return render(request, 'paste_detail.html', context)


def paste_download(request, paste_id):
    """Returns a zip with all the files."""
    paste = Paste.get_by_id(int(paste_id))
    if not paste:
        raise Http404

    filename = paste.filename.encode('latin-1') + '.zip'
    header = 'attachment; filename="%s"' % filename
    response = HttpResponse(content_type='application/zip')
    response['Content-disposition'] = header

    with zipfile.ZipFile(response, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
        for pasty_file in paste.files:
            name = pasty_file.filename

            with pasty_file.open() as fh:
                archive.writestr(name, fh.read())

    return response


def paste_create(request):
    fork_id = request.GET.get('fork')
    forked_from = Paste.get_by_id(int(fork_id)) if fork_id else None

    if request.method == 'POST':
        form = PasteForm(request.POST)

        if form.is_valid():
            paste = Paste(author=request.user_email, forked_from=forked_from)
            paste.description = form.cleaned_data['description']
            paste.put()

            filename_list = request.POST.getlist('filename')
            content_list = request.POST.getlist('content')

            for name, content in zip(filename_list, content_list):
                paste.save_content(content, filename=name)

            # Update the search index.
            index.add_paste(paste)

            return redirect('paste_detail', paste.key.id())
    else:
        if forked_from:
            with forked_from.files[0].open() as fh:
                content = fh.read()

            initial = {
                'filename': forked_from.filename,
                'description': forked_from.description,
                'content': content,
            }
        else:
            initial = {}
        form  = PasteForm(initial=initial)

    context = {
        'page_title': u'New paste',
        'form': form,
        'section': 'paste_create',
    }

    return render(request, 'paste_form.html', context)


def about(request):
    with open('CHANGELOG.md') as fh:
        text = fh.read()
        changelog = mistune.markdown(text)
        changelog = safestring.mark_safe(changelog)

    context = {
        'page_title': u'About',
        'section': 'about',
        'changelog': changelog,
    }

    return render(request, 'about.html', context)


def highlight_styles(request):
    content = u'\n\n'.join(css for _, css in utils.highlight_css.values())

    return HttpResponse(content, content_type='text/css')


def api_root(request):
    """Redirect to the most recent API index."""
    return redirect('api_index')


def api_index(request):
    """Info about the API endpoints."""
    patterns = utils.get_url_patterns('/api/v1')
    result = {'api': []}

    for name, pattern in patterns:
        link = request.build_absolute_uri(pattern)
        info = {
            'link': link,
            'name': name,
            'pattern': pattern,
        }

        result['api'].append(info)

    return JsonResponse(result)


@csrf_exempt
@require_http_methods(['POST'])
def api_star(request):
    """Adds the paste to the user's starred pastes (for POSTs)."""
    # N.B. we can ignore csrf because we check the user is signed-in.
    if not request.user_email:
        result = {u'error': u'Please sign in to star pastes'}
        return JsonResponse(result, status=403)

    paste_id = int(request.POST.get('paste'))
    paste = Paste.get_by_id(paste_id)
    if not paste:
        return JsonResponse({'error': 'Does not exist'}, status=400)

    # We construct the star id ourselves so that if you star something
    # twice it doesn't create multiple stars for the same paste.
    star_id = u'%s/%s' % (request.user_email, paste.key.id())
    starred = Star.get_or_insert(star_id, author=request.user_email, paste=paste.key)

    result = {
        'id': starred.key.id(),
        'author': starred.author,
        'paste': starred.paste.id(),
    }

    return JsonResponse(result)


def api_paste_list(request):
    if request.method == 'POST':
        return api_paste_create(request)

    per_page = 20
    pastes = Paste.objects.order_by('-created')
    paginator = Paginator(pastes, per_page)
    page_num = request.GET.get('p', 1)

    try:
        pastes = paginator.page(page_num)
    except InvalidPage:
        return redirect('api_paste_list')

    if pastes.has_next():
        next_page = '%s?p=%s' % (request.path, pastes.next_page_number())
        next_page = request.build_absolute_uri(next_page)
    else:
        next_page = None

    result = {
        'pastes': [p.to_dict() for p in pastes],
        'next': next_page,
    }

    return JsonResponse(result)


def api_paste_detail(request, paste_id):
    paste_id = int(paste_id)
    paste = Paste.get_by_id(paste_id)

    if not paste:
        result = {'error': 'Paste does not exist'}
        status = 404
    else:
        result = paste.to_dict()
        status = 200

    return JsonResponse(result, status=status)


@csrf_exempt
@require_http_methods(['POST'])
def api_paste_create(request):
    if not request.user_email:
        result = {u'error': u'Please sign in to create pastes'}

        return JsonResponse(result, status=403)

    try:
        data = json.load(request)
    except ValueError:
        result = {'error': 'Invalid request'}

        return JsonResponse(result, status=400)

    try:
        utils.paste_validator.validate(data)
    except jsonschema.ValidationError as err:
        result = {'error': err.message}

        return JsonResponse(result, status=400)

    first_file = data['files'][0]
    paste = Paste(
        author=request.user_email,
        description=data['description'],
        filename=first_file['filename'],
    )
    paste.put()
    paste.save_content(first_file['content'], filename=first_file['filename'])
    result = paste.to_dict()
    status = 201

    return JsonResponse(result, status=status)


def api_tag_list(request):
    return JsonResponse({})


def save_paste(paste):
    if not paste.filename:
        paste.filename = u''

    if not paste.description:
        paste.description = u''

    paste.save()
    index.add_paste(paste)


def admin(request):
    """Re-saves all the pastes."""
    from djangae.contrib.mappers.defer import defer_iteration

    if request.method == 'POST':
        queryset = Paste.objects.all()
        defer_iteration(queryset, save_paste)

    return render(request, 'admin.html')
