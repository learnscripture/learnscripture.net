"""
Handlers for AJAX requests.

This isn't really a REST API in the normal sense, and would probably need a lot
of cleaning up if clients other than the web app were to use it - we are just
using Piston for the convenience it provides.

"""
from django.utils.functional import wraps
from django.utils import simplejson

from piston.handler import BaseHandler
from piston.utils import rc

from accounts.models import Account
from bibleverses.models import UserVerseStatus, Verse
from learnscripture import session
from learnscripture.decorators import require_identity_method
from learnscripture.forms import SignUpForm, LogInForm


# We need a more capable 'validate' than the one provided by piston to get
# validation errors returned as JSON.

def validate(form_class, **formkwargs):
    def dec(method):
        @wraps(method)
        def wrapper(self, request, *args, **kwargs):
            form = form_class(request.POST, **formkwargs)
            if form.is_valid():
                request.form = form
                return method(self, request, *args, **kwargs)
            else:
                resp = rc.BAD_REQUEST
                resp.write("\n" + simplejson.dumps(form.errors))
                return resp
        return wrapper
    return dec


class NextVerseHandler(BaseHandler):
    allowed_methods = ('GET',)
    fields = ('id', 'memory_stage', 'strength', 'first_seen', 'last_seen',
              ('verse_choice', (('verse_set', ('id',)),)),
              ('verse', ('reference', 'text')),
              ('version', ('full_name', 'short_name', 'slug', 'url')))

    @require_identity_method
    def read(self, request):
        uvs_ids = session.get_verses_to_learn(request)
        if len(uvs_ids) == 0:
            return rc.NOT_FOUND

        try:
            return request.identity.verse_statuses.select_related('version', 'verse_choice', 'verse_choice__verse_set').get(id=uvs_ids[0])
        except UserVerseStatus.DoesNotExist:
            return rc.NOT_FOUND


class ActionCompleteHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_identity_method
    def create(self, request):
        uvs_id = int(request.data['user_verse_status_id'])
        try:
            uvs = request.identity.verse_statuses.get(id=uvs_id)
        except UserVerseStatus.DoesNotExist:
            return rc.NOT_FOUND

        # TODO: store StageComplete
        # TODO: update UserVerseStatus
        if request.data['stage'] == 'test':
            session.remove_user_verse_status(request, uvs_id)

        return {}


class ChangeVersionHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_identity_method
    def create(self, request):
        verse_set_id = request.data['verse_set_id']
        if verse_set_id == '' or verse_set_id == 'null':
            verse_set_id = None
        else:
            verse_set_id = int(verse_set_id)

        reference = request.data['reference']
        version_slug = request.data['version_slug']
        request.identity.change_version(reference,
                                        version_slug,
                                        verse_set_id)
        session.remove_user_verse_status(request, int(request.data['user_verse_status_id']))
        uvs = request.identity.verse_statuses.get(verse_choice__verse_set=verse_set_id,
                                                  verse_choice__reference=reference,
                                                  version__slug=version_slug)
        session.prepend_verse_statuses(request, [uvs])

        return {}


class AccountCommon(object):
    fields = ('id', 'username', 'email')


class SignUpHandler(AccountCommon, BaseHandler):
    allowed_methods = ('POST',)

    @require_identity_method
    @validate(SignUpForm, prefix="signup")
    def create(self, request):
        identity = request.identity
        if identity.account_id is not None:
            # UI should stop this happening.
            resp = rc.BAD_REQUEST
        account = request.form.save()
        identity.account = account
        identity.save()
        return account


class LogInHandler(AccountCommon, BaseHandler):
    allowed_methods = ('POST',)

    @validate(LogInForm, prefix="login")
    def create(self, request):
        # The form has validated the password already.
        account = Account.objects.get(email=request.form.cleaned_data['email'].strip())
        session.set_identity(request, account.identity)
        return account
