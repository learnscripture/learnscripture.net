"""
Handlers for AJAX requests.

This isn't really a REST API in the normal sense, and would probably need a lot
of cleaning up if clients other than the web app were to use it - we are just
using Piston for the convenience it provides.

"""
import logging

from django.utils.functional import wraps
from django.utils import simplejson

from piston.handler import BaseHandler
from piston.utils import rc

from accounts.models import Account
from bibleverses.models import UserVerseStatus, Verse, StageType, MAX_VERSES_FOR_SINGLE_CHOICE, InvalidVerseReference
from bibleverses.forms import VerseSelector
from learnscripture import session
from learnscripture.decorators import require_identity_method
from learnscripture.forms import SignUpForm, LogInForm
from learnscripture.utils.logging import extra


logger = logging.getLogger(__name__)
accountLogger = logging.getLogger('learnscripture.accounts')
learningLogger = logging.getLogger('learnscripture.learning')


# We need a more capable 'validate' than the one provided by piston to get
# validation errors returned as JSON.

def validation_error_response(errors):
    resp = rc.BAD_REQUEST
    resp.write("\n" + simplejson.dumps(errors))
    return resp


def validate(form_class, **formkwargs):
    def dec(method):
        @wraps(method)
        def wrapper(self, request, *args, **kwargs):
            if request.method == 'POST':
                data = request.POST
            else:
                data = request.GET
            form = form_class(data, **formkwargs)
            if form.is_valid():
                request.form = form
                return method(self, request, *args, **kwargs)
            else:
                return validation_error_response(form.errors)
        return wrapper
    return dec


class NextVerseHandler(BaseHandler):
    allowed_methods = ('GET',)
    fields = ('id', 'memory_stage', 'strength', 'first_seen',
              ('verse_choice', (('verse_set', ('id',)),)),
              'reference',
              'text',
              ('version', ('full_name', 'short_name', 'slug', 'url')))

    @require_identity_method
    def read(self, request):
        uvs_ids = session.get_verse_status_ids(request)
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
        learningLogger.info("Action %s complete", request.data.get('stage','[None]'), extra=extra(identity=request.identity, data=request.data))

        uvs_id = int(request.data['user_verse_status_id'])
        try:
            uvs = request.identity.verse_statuses.select_related('version', 'verse_choice').get(id=uvs_id)
        except UserVerseStatus.DoesNotExist:
            return rc.NOT_FOUND

        # TODO: store StageComplete
        stage = StageType.get_value_for_name(request.data['stage'])
        if  stage in [StageType.TEST_TYPE_FULL, StageType.TEST_TYPE_QUICK]:
            request.identity.record_verse_action(uvs.verse_choice.reference, uvs.version.slug,
                                                 stage, float(request.data['score']));
            session.remove_user_verse_status_id(request, uvs_id)

        return {}


class ChangeVersionHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_identity_method
    def create(self, request):
        verse_set_id = request.data['verse_set_id']
        if verse_set_id == '' or verse_set_id == 'null' or verse_set_id is None:
            verse_set_id = None
        else:
            verse_set_id = int(verse_set_id)

        reference = request.data['reference']
        version_slug = request.data['version_slug']
        request.identity.change_version(reference,
                                        version_slug,
                                        verse_set_id)
        session.remove_user_verse_status_id(request, int(request.data['user_verse_status_id']))
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
        accountLogger.info("New Account created", extra=extra(account=account))
        identity.account = account
        identity.save()
        return account


class LogInHandler(AccountCommon, BaseHandler):
    allowed_methods = ('POST',)

    @validate(LogInForm, prefix="login")
    def create(self, request):
        # The form has validated the password already.
        account = Account.objects.get(email=request.form.cleaned_data['email'].strip())
        session.login(request, account.identity)
        return account


class LogOutHandler(BaseHandler):
    allowed_methods = ('POST,')

    def create(self, request):
        session.logout(request)
        return {'username': 'Guest'}


class GetVerseForSelection(BaseHandler):
    allowed_methods = ('GET', )

    @require_identity_method
    @validate(VerseSelector, prefix='selection')
    def read(self, request):
        reference = request.form.make_reference()
        try:
            text = request.identity.default_bible_version.get_text_by_reference(reference, max_length=MAX_VERSES_FOR_SINGLE_CHOICE)

        except InvalidVerseReference as e:
            return validation_error_response({'__all__': e.message})
        return {'reference': reference,
                'text': text}
