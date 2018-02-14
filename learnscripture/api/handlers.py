# -*- coding: utf-8 -*-
"""
Handlers for AJAX requests.

This isn't really a REST API in the normal sense, and would probably need a lot
of cleaning up if clients other than the web app were to use it.
"""
import collections
import datetime
import json

import furl
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

        return lambda content: HttpResponse(r + "\n\n" + content,
                                            content_type='text/plain', status=c)


rc = rc_factory()


def require_preexisting_identity(view_func):
    """
    Returns a 400 error if there isn't already an identity
    """
    @wraps(view_func)
    def view(request, *args, **kwargs):
        # Assumes IdentityMiddleware
        if not hasattr(request, 'identity'):
            return rc.BAD_REQUEST("Identity required")
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
            return rc.BAD_REQUEST("Account required")
        return view_func(request, *args, **kwargs)
    return view


require_preexisting_account_m = method_decorator(require_preexisting_account)


def validation_error_response(errors):
    return HttpResponse(json.dumps(errors),
                        content_type='application/json',
                        status=400)


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
    def get_serializable(self, data):
        return make_serializable(data, getattr(self, 'fields', []))

    def dispatch(self, request, *args, **kwargs):
        retval = super(ApiView, self).dispatch(request, *args, **kwargs)
        if isinstance(retval, HttpResponse):
            return retval
        return HttpResponse(DjangoJSONEncoder().encode(
            self.get_serializable(retval)
        ), content_type='application/json')


class VersesToLearnHandler(ApiView):
    # NB: all of these fields get posted back to ActionCompleteHandler
    fields = [
        'id',
        'memory_stage', 'strength',
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
        return session.get_verse_statuses_batch(request).verse_statuses


class VersesToLearn2Handler(ApiView):
    @require_identity_method
    def get(sef, request):
        batch = session.get_verse_statuses_batch(request)
        verse_status_info = make_serializable(
            batch.verse_statuses,
            [
                'id',
                'memory_stage',
                'strength',
                'last_tested',
                'verse_set_id',
                'localized_reference',
                'needs_testing',
                'text_order',
                'suggestions',
                # added in get_verse_statuses:
                'version_slug',
                'scoring_text_words',
                'title_text',
                'learn_order',
            ])
        versions = make_serializable(
            set(vs.version for vs in batch.verse_statuses),
            ['full_name', 'short_name', 'slug', 'url', 'text_type']
        )
        # For verse sets additionally add 'smart_name' field, and include
        # version_id in link, so we don't just use make_serializable
        verse_sets_data = {}
        for vs in batch.verse_statuses:
            verse_set = vs.verse_set
            if verse_set is None:
                continue
            if verse_set.id in verse_sets_data:
                continue
            d = {
                "id": verse_set.id,
                "set_type": verse_set.set_type,
                "smart_name": verse_set.smart_name(vs.version.language_code),
                "url": furl.furl(verse_set.get_absolute_url()).add(
                    query_params={'version': vs.version.slug}).url
            }
            verse_sets_data[verse_set.id] = d

        retval = dict(
            verse_statuses=verse_status_info,
            learning_type=batch.learning_type,
            versions=list(versions),
            verse_sets=list(verse_sets_data.values()),
            return_to=batch.return_to,
            max_order_val=batch.max_order_val,
            untested_order_vals=batch.untested_order_vals,
        )
        if request.GET.get('initial_page_load', 'false') == 'true':
            # To reduce round trips and get the entire page loading in one go
            # initially, we hack these extra bits of data on here:
            retval['session_stats'] = dict(stats=todays_stats(request.identity))
            retval['action_logs'] = ActionLogs().get_serializable(
                request.identity.get_action_logs(
                    session.get_learning_session_start(request))
            )
        return retval


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

        # Get all inputs
        if 'verse_status' in request.POST:
            # Old /learn/ client page
            # Input here is a trimmed down version of what was sent by VersesToLearnHandler
            verse_status = get_verse_status(request.POST)
            uvs_id = verse_status['id']
            needs_testing = verse_status['needs_testing']
        else:
            # New /learn/ client page
            try:
                uvs_id = int(request.POST['uvs_id'])
                needs_testing = request.POST['uvs_needs_testing'] == 'true'
            except (KeyError, ValueError):
                return rc.BAD_REQUEST("uvs_id, uvs_needs_testing required")

        practice = request.POST.get('practice', 'false') == 'true'
        stage = StageType.check_value(request.POST['stage'])
        if stage == StageType.TEST:
            accuracy = float(request.POST['accuracy'])
        else:
            accuracy = None

        # Retrieve UVS
        try:
            uvs = request.identity.verse_statuses.get(id=uvs_id)
        except (KeyError, UserVerseStatus.DoesNotExist):
            return rc.BAD_REQUEST("valid verse_status id/uvs_id for user required")

        # Apply actions

        # If just practising, just remove the VS from the session.
        if practice:
            session.verse_status_finished(request, uvs_id, [])
            return {}

        old_memory_stage = uvs.memory_stage

        # TODO: ideally store StageComplete

        action_change = identity.record_verse_action(uvs.localized_reference, uvs.version.slug,
                                                     stage, accuracy)

        if action_change is None:
            # implies client error
            return rc.BAD_REQUEST("action_change required")

        action_logs = identity.award_action_points(uvs.localized_reference, uvs.scoring_text,
                                                   old_memory_stage,
                                                   action_change, stage, accuracy)

        if (stage == StageType.TEST or
                (stage == StageType.READ and not needs_testing)):
            session.verse_status_finished(request, uvs_id, action_logs)

        return {}


class SkipVerseHandler(ApiView):

    @require_preexisting_identity_m
    def post(self, request):
        if 'uvs_id' in request.POST:
            # New /learn/ page
            uvs_id = int(request.POST['uvs_id'])
        else:
            verse_status = get_verse_status(request.POST)
            uvs_id = verse_status['id']
        session.verse_status_skipped(request, uvs_id)
        return {}


class CancelLearningVerseHandler(ApiView):

    @require_preexisting_identity_m
    def post(self, request):
        if 'uvs_id' in request.POST:
            # New /learn/ page
            uvs_id = int(request.POST['uvs_id'])
            localized_reference = request.POST['localized_reference']
            version_slug = request.POST['version_slug']
        else:
            verse_status = get_verse_status(request.POST)
            uvs_id = verse_status['id']
            localized_reference = verse_status['localized_reference']
            version_slug = verse_status['version']['slug']
        request.identity.cancel_learning([localized_reference],
                                         version_slug)
        session.verse_status_cancelled(request, uvs_id)
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
        if 'localized_reference' in request.POST:
            # New /learn/ page
            localized_reference = request.POST['localized_reference']
            version_slug = request.POST['version_slug']
        else:
            verse_status = get_verse_status(request.POST)
            localized_reference = verse_status['localized_reference']
            version_slug = verse_status['version']['slug']
        request.identity.reset_progress(localized_reference,
                                        version_slug)
        return {}


class ReviewSoonerHandler(ApiView):

    @require_preexisting_identity_m
    def post(self, request):
        localized_reference = request.POST['localized_reference']
        version_slug = request.POST['version_slug']
        review_after = int(request.POST['review_after'])
        request.identity.review_sooner(localized_reference,
                                       version_slug,
                                       review_after)
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
        stats = todays_stats(identity)
        c.update(stats)
        retval['stats_html'] = render_to_string('learnscripture/sessionstats.html', c)
        retval['stats'] = stats
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
        highest_id_seen = int(request.GET.get('highest_id_seen', '0'))
        return request.identity.get_action_logs(session.get_learning_session_start(request),
                                                highest_id_seen=highest_id_seen)


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
            return rc.BAD_REQUEST("Parameters q, version_slug, passage_mode required")

        q = q.replace('—', '-').replace('–', '-')

        try:
            version = bible_versions_for_request(request).get(slug=version_slug)
        except TextVersion.DoesNotExist:
            return rc.BAD_REQUEST("Valid version required")

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


class AddVerseToQueue(ApiView):

    @require_preexisting_identity_m
    def post(self, request):
        identity = request.identity

        version = None
        try:
            version = TextVersion.objects.get(slug=request.POST['version_slug'])
        except (KeyError, TextVersion.DoesNotExist):
            return rc.BAD_REQUEST("Invalid version_slug")

        ref = request.POST.get('localized_reference', None)
        if ref is not None:
            # First ensure it is valid
            try:
                version.get_verse_list(ref, max_length=MAX_VERSES_FOR_SINGLE_CHOICE)
            except InvalidVerseReference:
                return rc.BAD_REQUEST("Invalid localized_reference")

            identity.add_verse_choice(ref, version=version)
            return {}
        else:
            return rc.BAD_REQUEST("No localized_reference")


class CheckDuplicatePassageSet(ApiView):

    def get(self, request):
        try:
            start_reference = request.GET['start_reference']
            end_reference = request.GET['end_reference']
        except KeyError:
            return rc.BAD_REQUEST("start_reference and end_reference required")

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
                     smart_name=vs.smart_name(language_code),
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
                return rc.BAD_REQUEST("Integer event_id required")

            try:
                event = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                return rc.BAD_REQUEST("Existing event_id required")

            comment = event.add_comment(author=account,
                                        message=message)

        elif 'group_id' in request.POST:
            try:
                group_id = int(request.POST['group_id'])
            except ValueError:
                return rc.BAD_REQUEST("Integer group_id required")

            try:
                group = Group.objects.visible_for_account(account).get(id=group_id)
            except Group.DoesNotExist:
                return rc.BAD_REQUEST("Existing group_id required")

            comment = group.add_comment(author=account,
                                        message=message)

        return comment


class HideComment(ApiView):

    @require_preexisting_account_m
    def post(self, request):
        if not request.identity.account.is_moderator:
            return rc.FORBIDDEN("Moderator account required")
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


class SaveMiscPreferences(ApiView):

    @require_preexisting_identity_m
    def post(self, request):
        identity = request.identity

        if 'heatmap_default_stats_type' in request.POST:
            identity.heatmap_default_stats_type = request.POST['heatmap_default_stats_type']
        if 'heatmap_default_show' in request.POST:
            identity.heatmap_default_show = request.POST['heatmap_default_show'] == 'true'
        if 'pin_action_log_menu_large_screen' in request.POST:
            identity.pin_action_log_menu_large_screen = request.POST['pin_action_log_menu_large_screen'] == 'true'
        if 'pin_action_log_menu_small_screen' in request.POST:
            identity.pin_action_log_menu_small_screen = request.POST['pin_action_log_menu_small_screen'] == 'true'
        identity.save()
        return {}
