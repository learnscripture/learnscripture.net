from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.functional import wraps
from django.utils.http import urlquote

from accounts.models import Identity

def require_identity(view_func):
    @wraps(view_func)
    def view(request, *args, **kwargs):
        identity = None
        identity_id = request.session.get('identity_id', None)
        if identity_id is not None:
            try:
                identity = Identity.objects.get(id=identity_id)
            except Identity.DoesNotExist:
                pass
        if identity is None:
            identity = Identity.objects.create()
        request.identity = identity
        if identity_id is None or identity.id != identity_id:
            request.session['identity_id'] = identity.id
        return view_func(request, *args, **kwargs)
    return view


def require_preferences(view_func):
    @wraps(view_func)
    @require_identity
    def view(request, *args, **kwargs):
        identity = request.identity
        if identity.default_bible_version is None:
            return HttpResponseRedirect(reverse('preferences') + "?next=%s" % urlquote(request.get_full_path()))
        return view_func(request, *args, **kwargs)
    return view
