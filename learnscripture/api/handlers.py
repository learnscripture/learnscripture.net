"""
Handlers for AJAX requests.

This isn't really a REST API in the normal sense, and would probably need a lot
of cleaning up if clients other than the web app were to use it - we are just
using Piston for the convenience it provides.

"""
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.functional import wraps
from django.utils import simplejson
from django.utils.decorators import method_decorator
from django.utils.html import escape, mark_safe

from piston.handler import BaseHandler
from piston.utils import rc

from accounts.forms import PreferencesForm
from accounts.models import Account
from bibleverses.models import StageType, MAX_VERSES_FOR_SINGLE_CHOICE, InvalidVerseReference, MAX_VERSE_QUERY_SIZE, TextVersion, quick_find, VerseSetType, UserVerseStatus
from comments.models import Comment
from events.models import Event
from groups.models import Group
from learnscripture import session
from learnscripture.decorators import require_identity_method
from learnscripture.views import session_stats, bible_versions_for_request, verse_sets_visible_for_request



def require_preexisting_identity(view_func):
    """
    Returns a 400 error if there isn't already an identity
    """
    @wraps(view_func)
    def view(request, *args, **kwargs):
        # Assumes IdentityMiddleware
        if not hasattr(request, 'identity'):
            return rc.BAD_REQUEST
        return view_func(request, *args, **kwargs)
    return view

require_preexisting_identity_m = method_decorator(require_preexisting_identity)


def require_preexisting_account(view_func):
    """
    Returns a 400 error if there isn't already an account
    """
    @wraps(view_func)
    def view(request, *args, **kwargs):
        # Assumes IdentityMiddleware
        if not hasattr(request, 'identity') or request.identity.account_id is None:
            return rc.BAD_REQUEST
        return view_func(request, *args, **kwargs)
    return view

require_preexisting_account_m = method_decorator(require_preexisting_account)

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
    fields = (
        'id',
        'memory_stage', 'strength', 'first_seen',
        ('verse_set', ('id', 'set_type', 'name', 'get_absolute_url')),
        'reference',
        'needs_testing',
        'text_order',
        ('version', ('full_name', 'short_name', 'slug', 'url', 'text_type')),
        'suggestions',
        # added in get_verse_statuses:
        'scoring_text_words',
        'title_text',
        'learn_order',
        'learning_type',
        'return_to',
        )

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
    verse_set = verse_status.get('verse_set', None)
    if verse_set is None:
        return None
    return verse_set.get('id', None)


class ActionCompleteHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_preexisting_identity_m
    def create(self, request):
        identity = request.identity

        # Input here is a trimmed down version of what was sent by VersesToLearnHandler
        verse_status = get_verse_status(request.data)
        if verse_status is None:
            return rc.BAD_REQUEST

        # Get everything we need, also applying security:
        try:
            uvs_id = verse_status['id']
            uvs = request.identity.verse_statuses.get(id=uvs_id)
        except (KeyError, UserVerseStatus.DoesNotExist):
            return rc.BAD_REQUEST

        # If just practising, just remove the VS from the session.
        practice = request.POST.get('practice', 'false') == 'true'
        if practice:
            session.verse_status_finished(request, uvs_id, [])
            return {}

        old_memory_stage = uvs.memory_stage

        # TODO: store StageComplete
        stage = StageType.get_value_for_name(request.data['stage'])
        if stage == StageType.TEST:
            accuracy = float(request.data['accuracy'])
        else:
            accuracy = None

        action_change = identity.record_verse_action(uvs.reference, uvs.version.slug,
                                                     stage, accuracy);

        if action_change is None:
            # implies client error
            return rc.BAD_REQUEST

        score_logs = identity.award_action_points(uvs.reference, uvs.scoring_text,
                                                  old_memory_stage,
                                                  action_change, stage, accuracy)

        if (stage == StageType.TEST or
            (stage == StageType.READ and not verse_status['needs_testing'])):
            session.verse_status_finished(request, verse_status['id'], score_logs)

        return {}


class RecordWordMistakes(BaseHandler):
    allowed_methods = ['POST']

    @require_preexisting_identity_m
    def create(self, request):
        ref = request.POST['reference']
        version_slug = request.POST['version']
        mistakes = simplejson.loads(request.POST['mistakes'])
        try:
            version = bible_versions_for_request(request).get(slug=version_slug)
        except TextVersion.DoesNotExist:
            return rc.BAD_REQUEST
        version.record_word_mistakes(ref, mistakes)
        return {}


class SkipVerseHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_preexisting_identity_m
    def create(self, request):
        verse_status = get_verse_status(request.data)
        session.verse_status_skipped(request, verse_status['id'])
        return {}


class CancelLearningVerseHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_preexisting_identity_m
    def create(self, request):
        verse_status = get_verse_status(request.data)
        reference = verse_status['reference']
        request.identity.cancel_learning([reference])
        session.verse_status_cancelled(request, verse_status['id'])
        return {}


class CancelLearningPassageHandler(BaseHandler):
    allowed_methods = ['POST']

    @require_preexisting_identity_m
    def create(self, request):
        vs_id = int(request.POST['verse_set_id'])
        request.identity.cancel_passage(vs_id)
        return {}


class ResetProgressHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_preexisting_identity_m
    def create(self, request):
        verse_status = get_verse_status(request.data)
        request.identity.reset_progress(verse_status['reference'],
                                        get_verse_set_id(verse_status),
                                        verse_status['version']['slug'])
        return {}


class ChangeVersionHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_preexisting_identity_m
    def create(self, request):
        verse_status = get_verse_status(request.data)
        verse_set_id = get_verse_set_id(verse_status)
        reference = verse_status['reference']
        new_version_slug = request.data['new_version_slug']
        # There is a bug here for the case where:
        # - user is learning a passage set
        # - user changes version to a version in which there are *more*
        #   verses for the passage, due to Verse.missing=True for some verses
        #   in the passage in the original version.
        #
        # This is not easy to fix, due to needing to replace a set of items
        # in the session learn queue with a longer set of items.

        replacements = request.identity.change_version(reference,
                                                       new_version_slug,
                                                       verse_set_id)
        session.replace_user_verse_statuses(request, replacements)
        return {}


class AccountCommon(object):
    fields = ('id', 'username', 'email')


class LogOutHandler(BaseHandler):
    allowed_methods = ('POST,')

    def create(self, request):
        import django.contrib.auth
        django.contrib.auth.logout(request)
        return {'username': 'Guest'}


class SetPreferences(BaseHandler):
    allowed_methods = ('POST',)
    fields = (
        ('default_bible_version', ('slug',)),
        'desktop_testing_method',
        'touchscreen_testing_method',
        'enable_animations',
        'enable_sounds',
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
        if not hasattr(request, 'identity'):
            return []
        return request.identity.get_score_logs(session.get_learning_session_start(request))



def html_format_text(verse):
    # Convert highlighted_text to HTML
    if hasattr(verse, 'highlighted_text'):
        t = verse.highlighted_text
    else:
        t = verse.text
    bits = t.split('**')
    out = []
    in_bold = False
    for b in bits:
        html = escape(b)
        if in_bold:
            html = u'<b>' + html + u'</b>'
        out.append(html)
        in_bold = not in_bold
    return mark_safe(u''.join(out))


class VerseFind(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request):
        try:
            q = request.GET['quick_find']
            version_slug = request.GET['version_slug']
            passage_mode = request.GET.get('passage_mode', '') == '1'
        except KeyError:
            return rc.BAD_REQUEST

        try:
            version = bible_versions_for_request(request).get(slug=version_slug)
        except TextVersion.DoesNotExist:
            return rc.BAD_REQUEST

        try:
            results = quick_find(q, version,
                                 max_length=MAX_VERSES_FOR_SINGLE_CHOICE
                                 if not passage_mode
                                 else MAX_VERSE_QUERY_SIZE,
                                 allow_searches=not passage_mode
                                 )
        except InvalidVerseReference as e:
            return validation_error_response({'__all__': [e.args[0]]})

        # Can't get 'fields' to work properly for this case, so pack into
        # dictionaries.
        retval = [dict(reference=r.reference,
                       text=r.text,
                       verses=r.verses)
                  for r in results]
        for item in retval:
            # Change 'verse' objects:
            verses2 = []
            for v in item['verses']:
                verses2.append(dict(
                        reference=v.reference,
                        text=v.text,
                        html_text=html_format_text(v),
                        book_number=v.book_number,
                        chapter_number=v.chapter_number,
                        verse_number=v.verse_number,
                        bible_verse_number=v.bible_verse_number
                        ))
            item['verses'] = verses2
            item['version_slug'] = version_slug
        return retval


class CheckDuplicatePassageSet(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request):
        try:
            passage_id = request.GET['passage_id']
        except KeyError:
            return rc.BAD_REQUEST

        verse_sets = verse_sets_visible_for_request(request)
        # This works if they have accepted default name.  If it doesn't have the
        # default name, it might not be considered a true 'duplicate' anyway.
        verse_sets = (verse_sets.filter(set_type=VerseSetType.PASSAGE,
                                        passage_id=passage_id,
                                        )
                      .select_related('created_by')
                      )
        return [dict(name=vs.name,
                     url=reverse('view_verse_set', args=[vs.slug]),
                     by=vs.created_by.username)
                for vs in verse_sets]


class DeleteNotice(BaseHandler):
    allowed_methods = ('POST',)

    @require_preexisting_identity_m
    def create(self, request):
        request.identity.notices.filter(id=int(request.data['id'])).delete()


class AndroidAppInstalled(BaseHandler):
    allowed_methods = ('POST',)

    def create(self, request):
        request.identity.account.android_app_installed()


class AddComment(BaseHandler):
    allowed_methods = ('POST',)
    fields = (
        ('author', ('id', 'username')),
        'event_id',
        'created',
        'message',
        'message_formatted',
        )

    @require_preexisting_account_m
    def create(self, request):
        account = request.identity.account

        if not account.enable_commenting:
            return {}

        message = request.POST.get('message', '').strip()
        if message == '':
            return validation_error_response({'message': 'You must enter a message'})

        comment = None
        if 'event_id' in request.POST:
            try:
                event_id = int(request.POST['event_id'])
            except ValueError:
                return rc.BAD_REQUEST

            try:
                event = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                return rc.BAD_REQUEST

            comment = event.add_comment(author=account,
                                        message=message)

        elif 'group_id' in request.POST:
            try:
                group_id = int(request.POST['group_id'])
            except ValueError:
                return rc.BAD_REQUEST

            try:
                group = Group.objects.visible_for_account(account).get(id=group_id)
            except Group.DoesNotExist:
                return rc.BAD_REQUEST

            comment = group.add_comment(author=account,
                                        message=message)

        return comment


class HideComment(BaseHandler):

    @require_preexisting_account_m
    def create(self, request):
        if not request.identity.account.is_moderator:
            return rc.FORBIDDEN
        Comment.objects.filter(id=int(request.POST['comment_id'])).update(hidden=True)
        return {}


class Follow(BaseHandler):

    @require_preexisting_account_m
    def create(self, request):
        account = Account.objects.get(id=int(request.POST['account_id']))
        request.identity.account.follow_user(account)
        return {}


class UnFollow(BaseHandler):

    @require_preexisting_account_m
    def create(self, request):
        account = Account.objects.get(id=int(request.POST['account_id']))
        request.identity.account.unfollow_user(account)
        return {}
