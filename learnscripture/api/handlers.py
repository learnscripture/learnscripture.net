# -*- coding: utf-8 -*-
"""
Handlers for AJAX requests.

This isn't really a REST API in the normal sense, and would probably need a lot
of cleaning up if clients other than the web app were to use it.
"""
import collections
import datetime
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import wraps
from django.utils.html import escape, mark_safe
from django.views.generic.base import View

from accounts.forms import PreferencesForm
from accounts.models import Account
from bibleverses.models import (MAX_VERSE_QUERY_SIZE, MAX_VERSES_FOR_SINGLE_CHOICE, InvalidVerseReference, StageType,
                                TextVersion, UserVerseStatus, VerseSetType, make_verse_set_passage_id, quick_find)
from bibleverses.parsing import internalize_localized_reference
from comments.models import Comment
from events.models import Event
from groups.models import Group
from learnscripture import session
from learnscripture.decorators import require_identity_method
from learnscripture.views import (bible_versions_for_request, default_bible_version_for_request, todays_stats,
                                  verse_sets_visible_for_request)


class rc_factory(object):
    """
    Status codes.
    """
    CODES = dict(ALL_OK=('OK', 200),
                 BAD_REQUEST=('Bad Request', 400),
                 FORBIDDEN=('Forbidden', 401),
                 )

    def __getattr__(self, attr):
        try:
            (r, c) = self.CODES.get(attr)
        except TypeError:
            raise AttributeError(attr)

        return HttpResponse(r, content_type='text/plain', status=c)


rc = rc_factory()


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


def validation_error_response(errors):
    resp = rc.BAD_REQUEST
    resp.write("\n" + json.dumps(errors))
    return resp


def get_instance_attr(instance, attr_name):
    retval = getattr(instance, attr_name)
    if isinstance(retval, collections.Callable):
        retval = retval()
    return retval


def instance_to_dict(instance, fields):
    if instance is None:
        return None
    retval = {}
    for field in fields:
        if isinstance(field, tuple):
            attr_name, sub_fields = field
            attr = get_instance_attr(instance, attr_name)
            retval[attr_name] = instance_to_dict(attr, sub_fields)
        else:
            retval[field] = get_instance_attr(instance, field)
    return retval


def make_serializable(value, fields=[]):
    if value is None:
        return value
    if isinstance(value, (str, int, float, datetime.date, datetime.datetime)):
        return value
    if isinstance(value, dict):
        return {k: make_serializable(v) for k, v in value.items()}
    if hasattr(value, '__iter__'):
        return [make_serializable(v, fields=fields) for v in value]
    return instance_to_dict(value, fields)


class ApiView(View):
    def dispatch(self, request, *args, **kwargs):
        retval = super(ApiView, self).dispatch(request, *args, **kwargs)
        if isinstance(retval, HttpResponse):
            return retval
        serializable = make_serializable(retval, getattr(self, 'fields', []))
        return HttpResponse(DjangoJSONEncoder().encode(serializable),
                            content_type='application/json')


class VersesToLearnHandler(ApiView):
    # NB: all of these fields get posted back to ActionCompleteHandler
    fields = [
        'id',
        'memory_stage', 'strength', 'first_seen',
        ('verse_set', ['id', 'set_type', 'name', 'get_absolute_url']),
        'localized_reference',
        'needs_testing',
        'text_order',
        ('version', ['full_name', 'short_name', 'slug', 'url', 'text_type']),
        'suggestions',
        # added in get_verse_statuses:
        'scoring_text_words',
        'title_text',
        'learn_order',
        'max_order_val',
        'learning_type',
        'return_to',
    ]

    @require_identity_method
    def get(self, request):
        return session.get_verse_statuses(request)


def get_verse_status(data):
    return json.loads(data['verse_status'])


def get_verse_set_id(verse_status):
    """
    Returns the verse set ID for a verse status dictionary (sent by client) or
    None if there is none
    """
    verse_set = verse_status.get('verse_set', None)
    if verse_set is None:
        return None
    return verse_set.get('id', None)


class ActionCompleteHandler(ApiView):

    @require_preexisting_identity_m
    def post(self, request):
        identity = request.identity

        # Input here is a trimmed down version of what was sent by VersesToLearnHandler
        verse_status = get_verse_status(request.POST)
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
        stage = StageType.get_value_for_name(request.POST['stage'])
        if stage == StageType.TEST:
            accuracy = float(request.POST['accuracy'])
        else:
            accuracy = None

        action_change = identity.record_verse_action(uvs.localized_reference, uvs.version.slug,
                                                     stage, accuracy)

        if action_change is None:
            # implies client error
            return rc.BAD_REQUEST

        action_logs = identity.award_action_points(uvs.localized_reference, uvs.scoring_text,
                                                   old_memory_stage,
                                                   action_change, stage, accuracy)

        if (stage == StageType.TEST or
                (stage == StageType.READ and not verse_status['needs_testing'])):
            session.verse_status_finished(request, verse_status['id'], action_logs)

        return {}


class SkipVerseHandler(ApiView):

    @require_preexisting_identity_m
    def post(self, request):
        verse_status = get_verse_status(request.POST)
        session.verse_status_skipped(request, verse_status['id'])
        return {}


class CancelLearningVerseHandler(ApiView):

    @require_preexisting_identity_m
    def post(self, request):
        verse_status = get_verse_status(request.POST)
        request.identity.cancel_learning([verse_status['localized_reference']],
                                         verse_status['version']['slug'])
        session.verse_status_cancelled(request, verse_status['id'])
        return {}


class CancelLearningPassageHandler(ApiView):

    @require_preexisting_identity_m
    def post(self, request):
        vs_id = int(request.POST['verse_set_id'])
        version_id = int(request.POST['version_id'])
        request.identity.cancel_passage(vs_id, version_id)
        return {}


class ResetProgressHandler(ApiView):

    @require_preexisting_identity_m
    def post(self, request):
        verse_status = get_verse_status(request.POST)
        request.identity.reset_progress(verse_status['localized_reference'],
                                        get_verse_set_id(verse_status),
                                        verse_status['version']['slug'])
        return {}


class AccountCommon(object):
    fields = ['id', 'username', 'email']


class LogOutHandler(ApiView):

    def post(self, request):
        import django.contrib.auth
        django.contrib.auth.logout(request)
        return {'username': 'Guest'}


class SetPreferences(ApiView):
    fields = [
        ('default_bible_version', ['slug']),
        'desktop_testing_method',
        'touchscreen_testing_method',
        'enable_animations',
        'enable_sounds',
        'enable_vibration',
        'interface_theme',
        'new_learn_page',
        'preferences_setup',
    ]

    @require_identity_method
    def post(self, request):
        form = PreferencesForm(request.POST, instance=request.identity)
        if form.is_valid():
            identity = form.save()
            return identity
        else:
            return validation_error_response(form.errors)


class SessionStats(ApiView):

    def get(self, request):
        if not hasattr(request, 'identity'):
            return {}

        identity = request.identity
        retval = {}

        # Render template
        c = {}
        c['identity'] = identity
        c.update(todays_stats(identity))
        retval['stats_html'] = render_to_string('learnscripture/sessionstats.html', c)
        return retval


class ActionLogs(ApiView):

    fields = [
        'id',  # used for uniqueness tests
        'points',
        'reason',
        'created',
    ]

    def get(self, request):
        if not hasattr(request, 'identity'):
            return []
        return request.identity.get_action_logs(session.get_learning_session_start(request))


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
            html = '<b>' + html + '</b>'
        out.append(html)
        in_bold = not in_bold
    return mark_safe(''.join(out).replace('\n', '<br>'))


class VerseFind(ApiView):

    def get(self, request):
        try:
            q = request.GET['quick_find']
            version_slug = request.GET['version_slug']
            passage_mode = request.GET.get('passage_mode', '') == '1'
        except KeyError:
            return rc.BAD_REQUEST

        q = q.replace('—', '-').replace('–', '-')

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
        retval = [dict(localized_reference=r.localized_reference,
                       internal_reference=r.internal_reference,
                       text=r.text,
                       from_reference=r.from_reference,
                       parsed_ref=None if r.parsed_ref is None else r.parsed_ref.__dict__,
                       verses=r.verses)
                  for r in results]
        for item in retval:
            # Change 'verse' objects:
            verses2 = []
            for v in item['verses']:
                verses2.append(dict(
                    localized_reference=v.localized_reference,
                    internal_reference=v.internal_reference,
                    text=v.text,
                    html_text=html_format_text(v),
                    book_number=v.book_number,
                    chapter_number=v.chapter_number,
                    display_verse_number=v.display_verse_number,
                    bible_verse_number=v.bible_verse_number
                ))
            item['verses'] = verses2
            item['version_slug'] = version_slug
        return retval


class CheckDuplicatePassageSet(ApiView):

    def get(self, request):
        try:
            start_reference = request.GET['start_reference']
            end_reference = request.GET['end_reference']
        except KeyError:
            return rc.BAD_REQUEST

        language_code = default_bible_version_for_request(request).language_code
        start_internal_reference = internalize_localized_reference(language_code, start_reference)
        end_internal_reference = internalize_localized_reference(language_code, end_reference)
        passage_id = make_verse_set_passage_id(start_internal_reference,
                                               end_internal_reference)

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


class DeleteNotice(ApiView):

    @require_preexisting_identity_m
    def post(self, request):
        request.identity.notices.filter(id=int(request.POST['id'])).delete()


class AddComment(ApiView):
    fields = [
        ('author', ['id', 'username']),
        'event_id',
        'created',
        'message',
        'message_formatted',
    ]

    @require_preexisting_account_m
    def post(self, request):
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


class HideComment(ApiView):

    @require_preexisting_account_m
    def post(self, request):
        if not request.identity.account.is_moderator:
            return rc.FORBIDDEN
        Comment.objects.filter(id=int(request.POST['comment_id'])).update(hidden=True)
        return {}


class Follow(ApiView):

    @require_preexisting_account_m
    def post(self, request):
        account = Account.objects.get(id=int(request.POST['account_id']))
        request.identity.account.follow_user(account)
        return {}


class UnFollow(ApiView):

    @require_preexisting_account_m
    def post(self, request):
        account = Account.objects.get(id=int(request.POST['account_id']))
        request.identity.account.unfollow_user(account)
        return {}
