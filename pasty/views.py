import mistune
from djangae.contrib.pagination import Paginator
from django.core.paginator import InvalidPage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse as render
from django.utils import safestring
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import index
from . import utils
from .forms import PasteForm
from .models import Paste, Star, get_starred_pastes


def paste_list(request):
    """Shows recent pastes."""
    per_page = 20
    pastes = Paste.objects.order_by('-created')
    paginator = Paginator(pastes, per_page)
    page_num = request.GET.get('p', 1)

    try:
        pastes = paginator.page(page_num)
    except InvalidPage:
        return redirect('paste_list')

    context = {
        'pastes': pastes,
        'section': 'paste_list',
        'starred_pastes': get_starred_pastes(request.user_email),
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

    query = index.build_query(request.GET)
    pastes = index.search_pastes(query, page) if query else []

    context = {
        'pastes': pastes,
        'section': 'paste_search',
        'starred_pastes': get_starred_pastes(request.user_email),
    }

    return render(request, 'paste_list.html', context)


def paste_detail(request, paste_id):
    paste = get_object_or_404(Paste, pk=paste_id)

    context = {
        'paste': paste,
        'starred_pastes': get_starred_pastes(request.user_email),
    }

    return render(request, 'paste_detail.html', context)


def paste_create(request):
    fork_id = request.GET.get('fork')

    try:
        forked_from = Paste.objects.get(pk=fork_id)
    except Paste.DoesNotExist:
        forked_from = None

    if request.method == 'POST':
        form = PasteForm(request.POST)

        if form.is_valid():
            paste = form.save(commit=False)
            paste.forked_from = forked_from
            paste.author = request.user_email
            paste.save()

            content = form.cleaned_data['content']
            filename = form.cleaned_data['filename']

            paste.save_content(content, filename)

            # Update the search index.
            index.add_paste(paste)

            return redirect('paste_list')
    else:
        if forked_from:
            initial = forked_from.__dict__
            initial['content'] = forked_from.files.first().content.read()
        else:
            initial = {}
        form  = PasteForm(initial=initial)

    context = {
        'form': form,
        'section': 'paste_create',
        'starred_pastes': get_starred_pastes(request.user_email),

    }

    return render(request, 'paste_form.html', context)


def about(request):
    with open('CHANGELOG.md') as fh:
        text = fh.read()
        changelog = mistune.markdown(text)
        changelog = safestring.mark_safe(changelog)

    context = {
        'section': 'about',
        'changelog': changelog,
    }

    return render(request, 'about.html', context)


def highlight_styles(request):
    content = u'\n\n'.join(utils.highlight_css.values())

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

    paste_id = request.POST.get('paste')
    try:
        paste = Paste.objects.get(pk=paste_id)
    except Paste.DoesNotExist:
        return JsonResponse({'error': 'Does not exist'}, status=400)

    # We construct the star id ourselves so that if you star something
    # twice it doesn't create multiple stars for the same paste.
    star_id = u'%s/%s' % (request.user_email, paste.pk)
    starred, _ = Star.objects.get_or_create(
        id=star_id,
        defaults = {
            'author': request.user_email,
            'paste_id': paste_id,
        }
    )

    result = {
        'id': starred.id,
        'author': starred.author,
        'paste': starred.paste_id,
    }

    return JsonResponse(result)


def api_paste_list(request):
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
    try:
        paste = Paste.objects.get(pk=paste_id)
    except Paste.DoesNotExist:
        result = {'error': 'Paste does not exist'}
        status = 404
    else:
        result = paste.to_dict()
        status = 200

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
