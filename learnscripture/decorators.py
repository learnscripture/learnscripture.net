from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils.functional import wraps
from django.utils.decorators import method_decorator
from django.utils.http import urlquote

from learnscripture import session


def require_identity(view_func):
    """
    Creates an identity if there is no identity active
    """
    @wraps(view_func)
    def view(request, *args, **kwargs):
        if not hasattr(request, 'identity'):
            identity = session.get_identity(request)
            if identity is None:
                identity = session.start_identity(request)
                request.identity = identity
        return view_func(request, *args, **kwargs)
    return view

require_identity_method = method_decorator(require_identity)


def has_preferences(request):
    identity = getattr(request, 'identity', None)
    if identity is None:
        return False
    return identity.preferences_setup


def redirect_via_prefs(request):
    return HttpResponseRedirect(reverse('preferences') + "?next=%s" % urlquote(request.get_full_path()))


def require_preferences(view_func):
    @wraps(view_func)
    def view(request, *args, **kwargs):
        if not has_preferences(request):
            return redirect_via_prefs(request)
        return view_func(request, *args, **kwargs)
    return view


def require_account(view_func):
    """
    Redirects to / if there is no account active
    """
    # NB this doesn't create an account.
    @wraps(view_func)
    def view(request, *args, **kwargs):
        if not hasattr(request, 'identity') or request.identity.account_id is None:
            return HttpResponseRedirect('/')
        return view_func(request, *args, **kwargs)
    return view


def require_account_with_redirect(view_func):
    """
    If there is no current account, show a page with links
    for logging in or creating an account.
    """
    @wraps(view_func)
    def view(request, *args, **kwargs):
        if not hasattr(request, 'identity') or request.identity.account_id is None:
            return render(request, 'learnscripture/login_and_redirect.html',
                          {'title': 'Login',
                           })
        return view_func(request, *args, **kwargs)
    return view
