from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import urlparse

from accounts.forms import PreferencesForm
from bibleverses.models import VerseSet, BibleVersion
from learnscripture import session

from .decorators import require_identity, require_preferences


@require_preferences
def learn(request):
    c = {'bible_versions': BibleVersion.objects.all()}
    return render(request, 'learnscripture/learn.html', c)


@require_identity
def preferences(request):
    if request.method == "POST":
        form = PreferencesForm(request.POST, instance=request.identity)
        if form.is_valid():
            form.save()
            messages.info(request, "Prefences updated, thank you.")
            return get_next(request, reverse('start'))
    else:
        form = PreferencesForm(instance=request.identity)
    c = {'form':form}
    return render(request, 'learnscripture/preferences.html', c)


def local_redirect(url):
    """
    Returns the URL if it is local, otherwise None
    """
    netloc = urlparse.urlparse(url)[1]
    return None if netloc else url


def get_next(request, default_url):
    if 'next' in request.GET:
        next = local_redirect(request.GET['next'])
        if next is not None:
            return HttpResponseRedirect(next)

    return HttpResponseRedirect(default_url)


@require_identity
def start(request):
    if not request.identity.verse_statuses.exists():
        # The only possible thing is to choose some verses
        return HttpResponseRedirect(reverse('choose'))

    # TODO

@require_preferences
def choose(request):
    """
    Choose a verse or verse set
    """
    if request.method == "POST":
        vs_id = request.POST.get('verseset_id', None)
        if vs_id is not None:
            try:
                vs = VerseSet.objects.prefetch_related('verse_choices').get(id=vs_id)
            except VerseSet.DoesNotExist:
                # Shouldn't be possible by clicking on buttons.
                pass
            if vs is not None:
                user_verse_statuses = request.identity.add_verse_set(vs)
                session.prepend_verse_statuses(request, user_verse_statuses)
                return HttpResponseRedirect(reverse('learn'))

    c = {}
    c['verse_sets'] = VerseSet.objects.all().order_by('name').prefetch_related('verse_choices')
    return render(request, 'learnscripture/choose.html', c)
