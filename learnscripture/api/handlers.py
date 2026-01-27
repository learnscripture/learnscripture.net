"""
Handlers for AJAX requests.

This isn't really a REST API in the normal sense, and would probably need a lot
of cleaning up if clients other than the web app were to use it.
"""

import csv
import datetime
import json
from datetime import date, timedelta
from io import StringIO

import furl
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.functional import wraps
from django.views.decorators.cache import never_cache
from django.views.generic.base import View

from accounts.forms import PreferencesForm
from accounts.models import Account, HeatmapStatsType, Identity
from bibleverses.models import (
    MAX_VERSE_QUERY_SIZE,
    MAX_VERSES_FOR_SINGLE_CHOICE,
    QUICK_FIND_SEARCH_LIMIT,
    InvalidVerseReference,
    StageType,
    TextVersion,
    UserVerseStatus,
    VerseSetType,
    make_verse_set_passage_id,
    quick_find,
)
from learnscripture import session
from learnscripture.decorators import require_identity_method
from learnscripture.ftl_bundles import t
from learnscripture.utils.templates import render_to_string_ftl
from learnscripture.views import bible_versions_for_request, todays_stats, verse_sets_visible_for_request
from scores.models import get_verses_started_per_day, get_verses_tested_per_day


class rc_factory:
    """
    Status codes.
    """

    CODES = dict(
        ALL_OK=("OK", 200),
        BAD_REQUEST=("Bad Request", 400),
        FORBIDDEN=("Forbidden", 401),
    )

    def __getattr__(self, attr):
        try:
            (r, c) = self.CODES.get(attr)
        except TypeError:
            raise AttributeError(attr)

        return lambda content: HttpResponse(r + "\n\n" + content, content_type="text/plain", status=c)


rc = rc_factory()


def require_preexisting_identity(view_func):
    """
    Returns a 400 error if there isn't already an identity
    """

    @wraps(view_func)
    def view(request, *args, **kwargs):
        # Assumes IdentityMiddleware
        if not hasattr(request, "identity"):
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
        if not hasattr(request, "identity") or request.identity.account_id is None:
            return rc.BAD_REQUEST("Account required")
        return view_func(request, *args, **kwargs)

    return view


require_preexisting_account_m = method_decorator(require_preexisting_account)


def validation_error_response(errors):
    return HttpResponse(json.dumps(errors), content_type="application/json", status=400)


def get_instance_attr(instance, attr_name):
    retval = getattr(instance, attr_name)
    if callable(retval):
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
    if isinstance(value, str | int | float | datetime.date | datetime.datetime):
        return value
    if isinstance(value, dict):
        return {k: make_serializable(v) for k, v in value.items()}
    if hasattr(value, "__iter__"):
        return [make_serializable(v, fields=fields) for v in value]
    return instance_to_dict(value, fields)


class ApiView(View):
    def get_serializable(self, data):
        return make_serializable(data, getattr(self, "fields", []))

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        retval = super().dispatch(request, *args, **kwargs)
        if isinstance(retval, HttpResponse):
            return retval
        return HttpResponse(DjangoJSONEncoder().encode(self.get_serializable(retval)), content_type="application/json")


class VersesToLearnHandler(ApiView):
    @require_identity_method
    def get(self, request):
        batch = session.get_verse_statuses_batch(request)
        verse_status_info = make_serializable(
            batch.verse_statuses,
            [
                "id",
                "memory_stage",
                "strength",
                "last_tested",
                "verse_set_id",
                "localized_reference",
                "needs_testing",
                "text_order",
                "prompt_list",
                # added in get_verse_statuses:
                "version_slug",
                "scoring_text_words",
                "test_text_words",
                "title_text",
                "learn_order",
            ],
        )
        versions = make_serializable(
            {vs.version for vs in batch.verse_statuses}, ["full_name", "short_name", "slug", "url", "text_type"]
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
                "url": furl.furl(verse_set.get_absolute_url()).add(query_params={"version": vs.version.slug}).url,
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
        if request.GET.get("initial_page_load", "false") == "true":
            # To reduce round trips and get the entire page loading in one go
            # initially, we hack these extra bits of data on here:
            retval["session_stats"] = dict(stats=todays_stats(request.identity))
            session_start = session.get_learning_session_start(request)
            if session_start is not None:
                retval["action_logs"] = ActionLogs().get_serializable(request.identity.get_action_logs(session_start))
        return retval


def get_verse_set_id(verse_status):
    """
    Returns the verse set ID for a verse status dictionary (sent by client) or
    None if there is none
    """
    verse_set = verse_status.get("verse_set", None)
    if verse_set is None:
        return None
    return verse_set.get("id", None)


class ActionCompleteHandler(ApiView):
    @require_preexisting_identity_m
    def post(self, request):
        identity: Identity = request.identity

        try:
            uvs_id = int(request.POST["uvs_id"])
            needs_testing = request.POST["uvs_needs_testing"] == "true"
        except (KeyError, ValueError):
            return rc.BAD_REQUEST("uvs_id, uvs_needs_testing required")

        practice = request.POST.get("practice", "false") == "true"
        try:
            stage = StageType(request.POST["stage"])
        except ValueError:
            return rc.BAD_REQUEST("Invalid value for stage")

        if stage == StageType.TEST:
            accuracy = float(request.POST["accuracy"])
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

        # TODO: combine record_verse_action and award_action_points
        action_change = identity.record_verse_action(uvs.localized_reference, uvs.version.slug, stage, accuracy)

        if action_change is None:
            # implies client error
            return rc.BAD_REQUEST("action_change required")

        action_logs = identity.award_action_points(
            uvs.localized_reference,
            uvs.version.language_code,
            uvs.scoring_text,
            old_memory_stage,
            action_change,
            stage,
            accuracy,
        )

        if stage == StageType.TEST or (stage == StageType.READ and not needs_testing):
            session.verse_status_finished(request, uvs_id, action_logs)

        return {}


class SkipVerseHandler(ApiView):
    @require_preexisting_identity_m
    def post(self, request):
        uvs_id = int(request.POST["uvs_id"])
        session.verse_status_skipped(request, uvs_id)
        return {}


class CancelLearningVerseHandler(ApiView):
    @require_preexisting_identity_m
    def post(self, request):
        uvs_id = int(request.POST["uvs_id"])
        localized_reference = request.POST["localized_reference"]
        version_slug = request.POST["version_slug"]
        request.identity.cancel_learning([localized_reference], version_slug)
        session.verse_status_cancelled(request, uvs_id)
        return {}


class CancelLearningPassageHandler(ApiView):
    @require_preexisting_identity_m
    def post(self, request):
        vs_id = int(request.POST["verse_set_id"])
        version_id = int(request.POST["version_id"])
        request.identity.cancel_passage(vs_id, version_id)
        return {}


class ResetProgressHandler(ApiView):
    @require_preexisting_identity_m
    def post(self, request):
        localized_reference = request.POST["localized_reference"]
        version_slug = request.POST["version_slug"]
        request.identity.reset_progress(localized_reference, version_slug)
        return {}


class ReviewSoonerHandler(ApiView):
    @require_preexisting_identity_m
    def post(self, request):
        localized_reference = request.POST["localized_reference"]
        version_slug = request.POST["version_slug"]
        review_after = int(request.POST["review_after"])
        request.identity.review_sooner(localized_reference, version_slug, review_after)
        return {}


class AccountCommon:
    fields = ["id", "username", "email"]


class SetPreferences(ApiView):
    fields = [
        ("default_bible_version", ["slug"]),
        "desktop_testing_method",
        "touchscreen_testing_method",
        "enable_animations",
        "enable_sounds",
        "enable_vibration",
        "interface_theme",
        "interface_language",
        "preferences_setup",
    ]

    def post(self, request):
        # Same song and dance as in views.preferences
        identity = getattr(request, "identity", None)
        form = PreferencesForm(request.POST, instance=identity)
        if form.is_valid():
            if identity is None:
                identity = session.start_identity(request)
                form = PreferencesForm(request.POST, instance=identity)
                identity = form.save()
                request.identity = identity
            else:
                identity = form.save()
            session.set_interface_language(request, identity.interface_language)
            return identity
        else:
            return validation_error_response(form.errors)


class SessionStats(ApiView):
    def get(self, request):
        if not hasattr(request, "identity"):
            return {}

        identity = request.identity
        return {"stats": todays_stats(identity)}


class ActionLogs(ApiView):
    fields = [
        "id",  # used for uniqueness tests
        "points",
        "reason",
        "created",
    ]

    def get(self, request):
        if not hasattr(request, "identity"):
            return []
        highest_id_seen = int(request.GET.get("highest_id_seen", "0"))
        session_start = session.get_learning_session_start(request)
        if session_start is None:
            return []
        else:
            return request.identity.get_action_logs(session_start, highest_id_seen=highest_id_seen)


class VerseFind(ApiView):
    def get(self, request):
        try:
            q = request.GET["quick_find"]
            version_slug = request.GET["version_slug"]
            passage_mode = request.GET.get("passage_mode", "") == "1"
            render_for = request.GET["render_for"]
            page = int(request.GET.get("page", "0"))
        except KeyError:
            return rc.BAD_REQUEST("Parameters q, version_slug, passage_mode, render_for required")

        TEMPLATES = {
            "create-selection-set": "learnscripture/create_selection_results_inc.html",
            "create-selection-row": "learnscripture/create_selection_row_inc.html",
            "create-passage-row": "learnscripture/create_passage_row_inc.html",
        }
        try:
            template_name = TEMPLATES[render_for]
        except KeyError:
            return rc.BAD_REQUEST(f"'render_for' parameter must be one of {', '.join(TEMPLATES.keys())}")

        q = q.replace("—", "-").replace("–", "-")

        try:
            version = bible_versions_for_request(request).get(slug=version_slug)
        except TextVersion.DoesNotExist:
            return rc.BAD_REQUEST("Valid version required")

        try:
            results, more_results = quick_find(
                q,
                version,
                max_length=MAX_VERSES_FOR_SINGLE_CHOICE if not passage_mode else MAX_VERSE_QUERY_SIZE,
                page=page,
                page_size=QUICK_FIND_SEARCH_LIMIT,
                allow_searches=not passage_mode,
                identity=getattr(request, "identity", None),
            )
        except InvalidVerseReference as e:
            return validation_error_response({"__all__": [e.args[0]]})

        if "single" in request.GET or passage_mode:
            results = results[0:1]
            more_results = False

        # Build context for rendering
        context = {
            "results": results,
            "version_slug": version_slug,
            "search_limit": QUICK_FIND_SEARCH_LIMIT,
            "more_results": more_results,
            "page": page,
            "next_page": page + 1,
        }

        if len(results) == 1 and results[0].parsed_ref is not None:
            parsed_reference = results[0].parsed_ref
        else:
            parsed_reference = None

        if passage_mode and len(results) == 1:
            duplicate_check_html = duplicate_passage_check(
                request,
                version.language_code,
                results[0].verses[0].internal_reference,
                results[0].verses[-1].internal_reference,
            )
        else:
            duplicate_check_html = None

        return {
            "html": render_to_string_ftl(template_name, context, request=request),
            "parsed_reference": parsed_reference.__dict__ if parsed_reference is not None else None,
            "canonical_reference": parsed_reference.canonical_form() if parsed_reference is not None else None,
            "passage_id": make_verse_set_passage_id(
                parsed_reference.get_start().to_internal(), parsed_reference.get_end().to_internal()
            )
            if parsed_reference is not None
            else None,
            "duplicate_check_html": duplicate_check_html,
        }


def duplicate_passage_check(request, language_code, start_internal_reference, end_internal_reference):
    passage_id = make_verse_set_passage_id(start_internal_reference, end_internal_reference)

    verse_sets = verse_sets_visible_for_request(request)
    verse_sets = verse_sets.filter(
        set_type=VerseSetType.PASSAGE, language_code=language_code, passage_id=passage_id
    ).select_related("created_by")

    if len(verse_sets) == 0:
        return ""
    else:
        context = {"verse_sets": verse_sets, "language_code": language_code}
        return render_to_string_ftl("learnscripture/duplicate_passage_warning_inc.html", context, request=request)


class SaveMiscPreferences(ApiView):
    @require_preexisting_identity_m
    def post(self, request):
        identity = request.identity

        if "heatmap_default_stats_type" in request.POST:
            identity.heatmap_default_stats_type = request.POST["heatmap_default_stats_type"]
        if "heatmap_default_show" in request.POST:
            identity.heatmap_default_show = request.POST["heatmap_default_show"] == "true"
        if "pin_action_log_menu_large_screen" in request.POST:
            identity.pin_action_log_menu_large_screen = request.POST["pin_action_log_menu_large_screen"] == "true"
        if "pin_action_log_menu_small_screen" in request.POST:
            identity.pin_action_log_menu_small_screen = request.POST["pin_action_log_menu_small_screen"] == "true"
        if "pin_verse_options_menu_large_screen" in request.POST:
            identity.pin_verse_options_menu_large_screen = request.POST["pin_verse_options_menu_large_screen"] == "true"
        if "seen_help_tour" in request.POST:
            identity.seen_help_tour = request.POST["seen_help_tour"] == "true"
        identity.save()
        return {}


class UserTimelineStats(ApiView):
    def get(self, request):
        try:
            username = request.GET["username"]
        except KeyError:
            raise Http404
        account = get_object_or_404(Account.objects.active().filter(username=username))
        identity = account.identity
        started = get_verses_started_per_day(identity.id)
        tested = get_verses_tested_per_day(account.id)

        rows = combine_timeline_stats(started, tested)

        # Add 'Combined' column
        rows2 = []
        for r in rows:
            newrow = list(r)
            newrow.append(sum(newrow[1:]))
            rows2.append(newrow)

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["Date", HeatmapStatsType.VERSES_STARTED, HeatmapStatsType.VERSES_TESTED, HeatmapStatsType.COMBINED]
        )
        for d, c1, c2, c3 in rows2:
            writer.writerow([d.strftime("%Y-%m-%d"), c1, c2, c3])

        streaks = {
            s: {
                "biggest": 0,
                "current": 0,
            }
            for s in HeatmapStatsType.values
        }

        def streaks_helper():
            for d, c1, c2, c3 in rows2:
                yield False, d, c1, c2, c3
            yield True, None, 0, 0, 0

        for last, d, c1, c2, c3 in streaks_helper():
            for stat, num in [
                (HeatmapStatsType.VERSES_STARTED, c1),
                (HeatmapStatsType.VERSES_TESTED, c2),
                (HeatmapStatsType.COMBINED, c3),
            ]:
                if num == 0:
                    if streaks[stat]["current"] > streaks[stat]["biggest"]:
                        streaks[stat]["biggest"] = streaks[stat]["current"]
                if not last:
                    if num == 0:
                        streaks[stat]["current"] = 0
                    else:
                        streaks[stat]["current"] += 1

        streaks_formatted = {
            stat: {n: t("heatmap-streak-length", {"days": val}) for n, val in streak.items()}
            for stat, streak in streaks.items()
        }
        return {
            "stats": output.getvalue(),
            "streaks": streaks,
            "streaks_formatted": streaks_formatted,
        }


def combine_timeline_stats(*statslists):
    # Each item in statslists is a sorted list containing a date object as first
    # item, and some other number as a second item. We zip together, based on
    # equality of dates, and supplying zero for missing items in any lists.
    retval = []
    num_lists = len(statslists)
    positions = [0] * num_lists  # current position in each of statslists
    statslist_r = list(range(0, num_lists))
    statslist_lengths = list(map(len, statslists))

    # Modify statslists to make end condition easier to handler
    for i in statslist_r:
        statslists[i].append((None, None))

    while any(positions[i] < statslist_lengths[i] for i in statslist_r):
        next_rows = [statslists[i][positions[i]] for i in statslist_r]
        next_dt_vals = [r[0] for r in next_rows if r[0] is not None]
        next_dt = min(next_dt_vals)
        rec = [0] * num_lists
        for i in statslist_r:
            dt, val = next_rows[i]
            if dt == next_dt:
                rec[i] = val
                positions[i] += 1
        rec.insert(0, next_dt)
        retval.append(rec)

    # Some things (calculating streaks client side) work correctly only if we
    # make sure that the data goes right up to today, or ends with a zero if it
    # doesn't.
    if len(retval) > 0:
        today = date.today()
        last_date = retval[-1][0]
        if last_date < today:
            next_day = last_date + timedelta(days=1)
            retval.append(tuple([next_day] + [0 for s in statslists]))

    return retval
