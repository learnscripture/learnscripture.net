from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import urlparse

from accounts.forms import PreferencesForm

from .decorators import require_identity, require_preferences


@require_preferences
def learn(request):
    return render(request, 'learnscripture/learn.html')


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



start = lambda: None
choose = lambda: None
