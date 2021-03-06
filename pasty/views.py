import json
import zipfile

import jsonschema
from djangae import environment
from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse as render
from django.views.decorators.http import require_http_methods
from google.appengine.ext import blobstore
from google.appengine.ext import ndb

from . import index
from . import utils
from . import validators
from .forms import AdminForm, AdminLexersFormSet, PasteForm
from .models import Paste, Star, get_starred_pastes


def home(request):
    return redirect('paste_create')


def paste_list(request):
    """Shows a synopsis of pastes.

    You can search for pastes by author and tag, or search the paste content.

    /?author=jeff@example.com - finds pastes by jeff@example.com
    /?q=foo - finds pastes containing the word 'foo'
    """
    page = request.GET.get('p')
    terms = index.build_query(request.GET)
    query = u' '.join(term for term, label, param in terms).encode('utf-8')
    pastes = index.search_pastes(query, page)
    tags = [label for term, label, param in terms]
    page_title = u'Pastes ' + u', '.join(tags)

    context = {
        'page_title': page_title,
        'pastes': pastes,
        'section': 'paste_list',
        'terms': terms,
    }

    return render(request, 'pasty/paste_list.html', context)


def paste_redirect(request, paste_code):
    """Redirect from old peelings links."""
    paste_id = utils.base62.decode(paste_code)
    url = redirect('paste_detail', paste_id)

    return url


def paste_detail(request, paste_id):
    paste = Paste.get_or_404(paste_id)

    starred = Star.query(Star.author==request.user_email, Star.paste==paste.key).get()

    context = {
        'page_title': paste.filename,
        'paste': paste,
        'starred': starred,
    }

    return render(request, 'pasty/paste_detail.html', context)


def paste_download(request, paste_id):
    """Returns a zip with all the files."""
    paste = Paste.get_or_404(paste_id)

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


def paste_raw(request, paste_id, relative_path):
    """Serve a file in Google Cloud Storage using the blobstore API."""
    paste = Paste.get_or_404(paste_id)

    for pasty_file in paste.files:
        if pasty_file.relative_path == relative_path:
            break
    else:
        raise Http404

    blob_key = blobstore.create_gs_key('/gs' + pasty_file.bucket_path())
    response = HttpResponse(content_type=pasty_file.content_type)
    response[blobstore.BLOB_KEY_HEADER] = str(blob_key)

    return response


def paste_create(request):
    """Make a new Paste.

    Add ?fork=xyz to a GET request and the initial form will have an existing
    Paste's contents.
    """
    fork_id = request.GET.get('fork')
    fork = Paste.get_by_id(int(fork_id)) if fork_id else None

    if request.method == 'POST':
        form = PasteForm(request.POST)

        if form.is_valid():
            author = request.user_email
            description = form.cleaned_data['description']
            filename_list = request.POST.getlist('filename')
            content_list = request.POST.getlist('content')
            files = zip(filename_list, content_list)

            paste = Paste.create_with_files(
                author=author, fork=fork, description=description, files=files)

            # Update the search index.
            index.add_paste(paste)

            return redirect('paste_detail', paste.key.id())
    else:
        if fork:
            with fork.files[0].open() as fh:
                content = fh.read()

            initial = {
                'filename': fork.filename,
                'description': fork.description,
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

    return render(request, 'pasty/paste_form.html', context)


def api_star_list(request):
    """Show what pastes the current user has starred (if any)."""
    if not request.user_email:
        result = {u'error': u'Please sign in to star pastes'}
        return JsonResponse(result, status=403)

    result = {
        'stars': [p.to_dict() for p in get_starred_pastes(request.user_email)],
    }

    return JsonResponse(result)


@require_http_methods(['POST'])
def api_star_create(request):
    """Adds the paste to the user's starred pastes (for POSTs)."""
    # N.B. we can ignore csrf because we check the user is signed-in.
    if not request.user_email:
        result = {u'error': u'Please sign in to star pastes'}
        return JsonResponse(result, status=403)

    try:
        paste = Paste.get_or_404(request.POST.get('paste'))
    except Http404:
        return JsonResponse({'error': 'Does not exist'}, status=400)

    starred = paste.create_star_for_author(request.user_email)

    result = {
        'id': starred.key.id(),
        'author': starred.author,
        'paste': starred.paste.id(),
        'stars': [p.to_dict() for p in get_starred_pastes(request.user_email)],
    }

    return JsonResponse(result)


@require_http_methods(['POST'])
def api_star_delete(request):
    if not request.user_email:
        result = {u'error': u'Please sign in to star pastes'}
        return JsonResponse(result, status=403)

    try:
        paste = Paste.get_or_404(request.POST.get('paste'))
    except Http404:
        return JsonResponse({'error': 'Does not exist'}, status=400)

    star_id = u'%s/%s' % (request.user_email, paste.key.id())
    star_key = ndb.Key(Star, star_id)
    star_key.delete()

    result = {
        'id': star_key.id(),
        'stars': [p.to_dict() for p in get_starred_pastes(request.user_email)],
    }

    return JsonResponse(result)


def api_paste_list(request):
    if request.method == 'POST':
        return api_paste_create(request)

    page = request.GET.get('p')
    terms = index.build_query(request.GET)
    query = u' '.join(term for term, label, param in terms).encode('utf-8')
    pastes = index.search_pastes(query, page)

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
    try:
        paste = Paste.get_or_404(paste_id)
    except Http404:
        result = {'error': 'Paste does not exist'}
        status = 404
    else:
        result = paste.to_dict()
        status = 200

    return JsonResponse(result, status=status)


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
        validators.paste_validator.validate(data)
    except jsonschema.ValidationError as err:
        result = {'error': err.message}

        return JsonResponse(result, status=400)

    files = [(f['filename'], f['content']) for f in data['files']]
    paste = Paste.create_with_files(
        author=request.user_email, description=data['description'], files=files)

    index.add_paste(paste)

    result = paste.to_dict()
    status = 201

    return JsonResponse(result, status=status)


@environment.task_or_admin_only
def admin(request):
    """For firing migration tasks."""
    form = AdminForm()

    if request.method == 'POST':
        form = AdminForm(request.POST)

        if form.is_valid():
            for label, task_func in form.cleaned_data['tasks']:
                task_func()
                msg = u'Started "%s" task\u2026' % label.lower()
                messages.success(request, msg)

                return redirect('admin')

    context = {
        'form': form,
        'section': 'admin',
        'page_title': u'Administration things',
    }
    return render(request, 'pasty/admin.html', context)


@environment.task_or_admin_only
def admin_lexers(request):
    """Form to configure lexers for file extensions."""
    formset = AdminLexersFormSet.for_config()

    if request.method == 'POST':
        formset = AdminLexersFormSet.for_config(request.POST)

        if formset.is_valid():
            formset.save()
            messages.success(request, u'Saved configuration')

            return redirect('admin_lexers')

    context = {
        'formset': formset,
        'section': admin,
        'page_title': u'Configure highlighting',
    }

    return render(request, 'pasty/admin_lexers.html', context)
