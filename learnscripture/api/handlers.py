"""
Handlers for AJAX requests.

This isn't really a REST API in the normal sense, and would probably need a lot
of cleaning up if clients other than the web app were to use it - we are just
using Piston for the convenience it provides.

"""
import logging

from django.template.loader import render_to_string
from django.utils.functional import wraps
from django.utils import simplejson

from piston.handler import BaseHandler
from piston.utils import rc

from accounts.forms import PreferencesForm
from accounts.models import Account
from bibleverses.models import UserVerseStatus, Verse, StageType, MAX_VERSES_FOR_SINGLE_CHOICE, InvalidVerseReference, MAX_VERSE_QUERY_SIZE
from bibleverses.forms import VerseSelector, PassageVerseSelector
from learnscripture import session
from learnscripture.decorators import require_identity_method
from learnscripture.forms import SignUpForm, LogInForm
from learnscripture.utils.logging import extra
from learnscripture.views import session_stats


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


class VersesToLearnHandler(BaseHandler):
    allowed_methods = ('GET',)
    # NB: all of these fields get posted back to ActionCompleteHandler
    fields = ('memory_stage', 'strength', 'first_seen',
              ('verse_choice', (('verse_set', ('id', 'set_type')),)),
              'reference',
              'text',
              'needs_testing',
              'learn_order',
              ('version', ('full_name', 'short_name', 'slug', 'url')))

    @require_identity_method
    def read(self, request):
        return session.get_verse_statuses(request)


def get_verse_status(data):
    return simplejson.loads(data['verse_status'])


def get_verse_set_id(verse_status):
    """
    Returns the verse set ID for a verse status dictionary (sent by client) or
    None if there is none
    """
    verse_choice = verse_status['verse_choice']
    verse_set = verse_choice.get('verse_set', None)
    if verse_set is None:
        return None
    return verse_set.get('id', None)


class ActionCompleteHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_identity_method
    def create(self, request):
        identity = request.identity
        learningLogger.info("Action %s complete", request.data.get('stage','[None]'), extra=extra(identity=identity, data=request.data, request=request))

        verse_status = get_verse_status(request.data)
        reference = verse_status['reference']
        version_slug = verse_status['version']['slug']
        verse_set_id = get_verse_set_id(verse_status)

        # TODO: store StageComplete
        stage = StageType.get_value_for_name(request.data['stage'])
        if stage == StageType.TEST:
            accuracy = float(request.data['accuracy'])
        else:
            accuracy = None

        action_change = identity.record_verse_action(reference, version_slug,
                                                     stage, accuracy);
        score_logs = identity.award_action_points(reference, verse_status['text'],
                                                  verse_status['memory_stage'],
                                                  action_change, stage, accuracy)
        if (stage == StageType.TEST or
            (stage == StageType.READ and not verse_status['needs_testing'])):
            session.verse_status_finished(request, reference, verse_set_id, score_logs)

        return {}


class SkipVerseHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_identity_method
    def create(self, request):
        verse_status = get_verse_status(request.data)
        verse_set_id = get_verse_set_id(verse_status)
        session.verse_status_skipped(request, verse_status['reference'], verse_set_id)
        return {}


class CancelLearningVerseHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_identity_method
    def create(self, request):
        verse_status = get_verse_status(request.data)
        verse_set_id = get_verse_set_id(verse_status)
        reference = verse_status['reference']
        request.identity.cancel_learning(reference)
        session.verse_status_cancelled(request, reference, verse_set_id)
        return {}


class ChangeVersionHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_identity_method
    def create(self, request):
        verse_status = get_verse_status(request.data)
        verse_set_id = get_verse_set_id(verse_status)
        reference = verse_status['reference']
        new_version_slug = request.data['new_version_slug']
        request.identity.change_version(reference,
                                        new_version_slug,
                                        verse_set_id)
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
        accountLogger.info("New Account created", extra=extra(account=account, request=request))
        identity.account = account
        identity.save()
        return account


class LogInHandler(AccountCommon, BaseHandler):
    allowed_methods = ('POST',)

    @validate(LogInForm, prefix="login")
    def create(self, request):
        # The form has validated the password already.
        account = Account.objects.get(email__iexact=request.form.cleaned_data['email'].strip())
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
            return validation_error_response({'__all__': [e.message]})
        return {'reference': reference,
                'text': text}

class GetPassage(BaseHandler):
    allowed_methods = ('GET', )

    @require_identity_method
    @validate(PassageVerseSelector, prefix='passage')
    def read(self, request):
        reference = request.form.make_reference()
        try:
            verse_list = request.identity.default_bible_version.get_verse_list(reference,
                                                                               max_length=MAX_VERSE_QUERY_SIZE)

        except InvalidVerseReference as e:
            return validation_error_response({'__all__': [e.message]})
        return {'reference': reference,
                'verse_list': [{'reference': v.reference, 'text': v.text} for v in verse_list]}


class SetPreferences(BaseHandler):
    allowed_methods = ('POST',)
    fields = (
        ('default_bible_version', ('slug',)),
        'testing_method',
        'enable_animations',
        'interface_theme',
        'preferences_setup',
        )

    @require_identity_method
    def create(self, request):
        form = PreferencesForm(request.POST, instance=request.identity)
        if form.is_valid():
            identity = form.save()
            return identity
        else:
            return validation_error_response(form.errors)


class SessionStats(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request):
        if not hasattr(request, 'identity'):
            return {}

        identity = request.identity
        retval = {}

        # Render template
        c = {}
        c['identity'] = identity
        c.update(session_stats(identity))
        retval['stats_html'] = render_to_string('learnscripture/sessionstats.html', c)
        return retval


class ScoreLogs(BaseHandler):
    allowed_methods = ('GET',)

    fields = (
        'id', # used for uniqueness tests
        'points',
        'reason',
        'created',
        )

    def read(self, request):
        return request.identity.get_score_logs(session.get_learning_session_start(request))

