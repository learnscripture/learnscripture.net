from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.functional import wraps
from django.utils.decorators import method_decorator
from django.utils.http import urlquote

from learnscripture import session


def require_identity(view_func):
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


def require_preferences(view_func):
    @wraps(view_func)
    @require_identity
    def view(request, *args, **kwargs):
        identity = request.identity
        if identity.default_bible_version is None:
            return HttpResponseRedirect(reverse('preferences') + "?next=%s" % urlquote(request.get_full_path()))
        return view_func(request, *args, **kwargs)
    return view
