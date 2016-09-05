from djangae.contrib.pagination import Paginator
from django.core.paginator import InvalidPage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse as render

from . import index
from . import utils
from .forms import PasteForm
from .models import Paste, Tag


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
    pastes = index.search_pastes(query, page)

    context = {
        'pastes': pastes,
        'section': 'paste_search',
    }

    return render(request, 'paste_list.html', context)


def paste_detail(request, paste_id):
    paste = get_object_or_404(Paste, pk=paste_id)

    return render(request, 'paste_detail.html', {'paste': paste})


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
            paste.author = utils.get_current_user_email()
            paste.save()

            # Update the search index.
            index.add_paste(paste)

            return redirect('paste_list')
    else:
        initial = forked_from.__dict__ if forked_from else {}
        form  = PasteForm(initial=initial)

    context = {
        'form': form,
        'section': 'paste_create',
    }

    return render(request, 'paste_form.html', context)


def tag_list(request):
    tags = Tag.objects.all()
    context = {
        'tags': tags,
        'section': 'tag_list',
    }

    return render(request, 'tag_list.html', context)


def about(request):
    context = {'section': 'about'}

    return render(request, 'about.html', context)


def highlight_styles(request):
    content = u'\n\n'.join(utils.highlight_css.values())

    return HttpResponse(content, content_type='text/css')


def api_paste_list(request):
    return ''


def api_paste_detail(request, paste_id):
    return ''


def api_tag_list(request):
    return ''


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
