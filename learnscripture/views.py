import urllib.parse
from datetime import timedelta

import furl
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView as AuthPasswordResetView
from django.contrib.sites.models import Site
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.views import i18n as i18n_views
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from django.views.defaults import server_error
from paypal.standard.forms import PayPalPaymentsForm

import learnscripture.tasks
from accounts.forms import AccountDetailsForm, PreferencesForm
from accounts.models import Account, HeatmapStatsType, Identity, get_account_stats
from awards.models import AWARD_LOGIC_CLASSES, AnyLevel, Award, AwardType
from bibleverses.books import BIBLE_BOOK_COUNT, get_bible_book_name
from bibleverses.forms import VerseSetForm
from bibleverses.languages import LANGUAGE_CODE_INTERNAL, LANGUAGES
from bibleverses.models import (
    MAX_VERSES_FOR_SINGLE_CHOICE,
    InvalidVerseReference,
    TextType,
    TextVersion,
    VerseChoice,
    VerseSet,
    VerseSetType,
    get_passage_sections,
    is_continuous_set,
    verse_set_passage_id_to_parsed_ref,
)
from bibleverses.parsing import (
    localize_internal_reference,
    parse_break_list,
    parse_unvalidated_localized_reference,
    parse_validated_internal_reference,
)
from bibleverses.signals import public_verse_set_created
from events.models import Event
from groups.forms import EditGroupForm
from groups.models import Group
from groups.signals import public_group_created
from learnscripture import session
from learnscripture.forms import (
    FILTER_LANGUAGES_ALL,
    GROUP_WALL_ORDER_OLDEST_FIRST,
    LEADERBOARD_WHEN_THIS_WEEK,
    USER_VERSES_ORDER_STRONGEST,
    USER_VERSES_ORDER_WEAKEST,
    VERSE_SET_ORDER_AGE,
    VERSE_SET_ORDER_POPULARITY,
    VERSE_SET_TYPE_ALL,
    AccountPasswordChangeForm,
    AccountPasswordResetForm,
    AccountSetPasswordForm,
    GroupFilterForm,
    GroupWallFilterForm,
    LeaderboardFilterForm,
    LogInForm,
    SignUpForm,
    UserVersesFilterForm,
    VerseSetSearchForm,
)
from learnscripture.ftl_bundles import t
from payments.sign import sign_payment_info
from scores.models import get_all_time_leaderboard, get_leaderboard_since, get_verses_started_counts

from .decorators import (
    for_htmx,
    has_preferences,
    redirect_via_prefs,
    require_account,
    require_account_with_redirect,
    require_identity,
    require_preferences,
)
from .utils.paging import Page, get_paged_results, get_request_from_item
from .utils.urls import build_signup_url

#
# === Notes ===
#
# Care is needed with identity/account:
#
# - see notes in accounts/models.py for the distinction
#
# - we try to avoid creating Identity objects until we need to, so that
#   bots like web crawlers don't cause database inserts
#
# - if there is no current 'Identity' the user will appear
#   as 'Guest' (menu in base.html)
# - if there is an Identity, but no Account, they will still
#   appear as 'Guest user', but now have the possibility of stored
#   data and preferences.
#
# - We do need Identity and preferences to be set for some actions,
#   so we create it as needed, typically by the popup preferences form


USER_EVENTS_SHORT_CUTOFF = 5
GROUP_COMMENTS_SHORT_CUTOFF = 5
GROUP_COMMENTS_PAGINATE_BY = 40


def missing(request, message, status_code=404):
    response = TemplateResponse(request, "404.html", {"message": message})
    response.status_code = status_code
    return response


def test_500(request):
    return handler500(request)


def test_500_real(request):
    1 / 0


def handler500(request):
    return server_error(request)


def home(request):
    identity = getattr(request, "identity", None)
    if identity is not None and identity.default_to_dashboard:
        return HttpResponseRedirect(reverse("dashboard"))
    return TemplateResponse(request, "learnscripture/home.html")


def _login_redirect(request):
    return get_next(request, reverse("dashboard"))


def login(request):
    if account_from_request(request) is not None:
        return _login_redirect(request)

    if request.method == "POST":
        form = LogInForm(request.POST, prefix="login")
        if "signin" in request.POST:
            if form.is_valid():
                account = form.cleaned_data["account"]
                account.last_login = timezone.now()
                account.save()
                session.login(request, account.identity)
                return _login_redirect(request)
        elif "forgotpassword" in request.POST:
            resetform = AccountPasswordResetForm(request.POST, prefix="login")
            if resetform.is_valid():
                # This will validate the form again, but it doesn't matter.
                return password_reset(request)
            else:
                # Need errors from password reset for be used on main form - hack
                form._errors = resetform.errors
    else:
        form = LogInForm(prefix="login")

    return TemplateResponse(
        request,
        "learnscripture/login.html",
        {
            "title": "Sign in",
            "login_form": form,
        },
    )


class _PasswordResetView(AuthPasswordResetView):
    form_class = AccountPasswordResetForm
    email_template_name = "learnscripture/password_reset_email.txt"
    subject_template_name = "learnscripture/password_reset_subject.txt"

    def get_prefix(self):
        return "login"


password_reset = _PasswordResetView.as_view()


def signup(request):
    from accounts.signals import new_account

    ctx = {}
    if account_from_request(request) is not None:
        ctx["already_signed_up"] = True

    if request.method == "POST":
        form = SignUpForm(request.POST, prefix="signup")

        if form.is_valid():
            identity = getattr(request, "identity", None)
            if identity is None or identity.account_id is not None:
                # Need to create a new identity if one doesn't exist,
                # or the current one is assigned to an existing user.
                identity = session.start_identity(request)
            account = form.save(commit=False)
            account.last_login = timezone.now()
            account.save()
            account.identity = identity
            identity.account = account
            identity.save()
            session.login(request, account.identity)
            messages.info(request, t("accounts-signup-welcome-notice", dict(username=account.username)))
            new_account.send(sender=account)
            return _login_redirect(request)

    else:
        form = SignUpForm(prefix="signup")

    ctx["title"] = t("accounts-signup-title")
    ctx["signup_form"] = form

    return TemplateResponse(request, "learnscripture/signup.html", ctx)


def bible_versions_for_request(request):
    return TextVersion.objects.bibles().visible_for_identity(getattr(request, "identity", None))


@require_preferences
def learn(request):
    return TemplateResponse(request, "learnscripture/learn.html", {})


def preferences(request):
    # See also api.handlers.SetPreferences
    identity = getattr(request, "identity", None)
    if request.method == "POST":
        form = PreferencesForm(request.POST, instance=identity)
        if form.is_valid():
            if identity is None:
                # This little routine is needed so that
                # we can start the identity in the standard
                # way, yet, don't create an identity until
                # they press the 'save' button.
                identity = session.start_identity(request)
                form = PreferencesForm(request.POST, instance=identity)
                request.identity = identity
            form.save()
            session.set_interface_language(request, identity.interface_language)
            return get_next(request, reverse("dashboard"))
    else:
        form = PreferencesForm(instance=identity)
    ctx = {
        "form": form,
        "title": t("accounts-preferences-title"),
        "hide_preferences_popup": True,
    }
    return TemplateResponse(request, "learnscripture/preferences.html", ctx)


def account_from_request(request):
    if hasattr(request, "identity"):
        return request.identity.account
    else:
        return None


def local_redirect(url):
    """
    Returns the URL if it is local, otherwise None
    """
    netloc = urllib.parse.urlparse(url)[1]
    return None if netloc else url


def get_next(request, default_url):
    if "next" in request.GET:
        next = local_redirect(request.GET["next"])
        if next is not None:
            return HttpResponseRedirect(next)

    return HttpResponseRedirect(default_url)


def todays_stats(identity):
    return {
        "total_verses_tested": identity.verse_statuses.total_tested_today_count(),
        "new_verses_started": identity.verse_statuses.started_today_count(),
    }


def learn_set(request, uvs_list, learning_type):
    uvs_list = [u for u in uvs_list if u is not None]
    # Save where we should return to after learning:
    return_to = reverse("dashboard")  # by default, the dashboard
    referer = request.headers.get("Referer")
    if referer is not None:
        url = urllib.parse.urlparse(referer)
        allowed_return_to = [reverse("user_verses")]  # places it is useful to return to
        if url.path in allowed_return_to:
            # avoiding redirection security problems by making it relative:
            url = ("", "", url.path, url.params, url.query, url.fragment)
            return_to = urllib.parse.urlunparse(url)

    session.start_learning_session(request, uvs_list, learning_type, return_to)

    return HttpResponseRedirect(get_learn_page(request))


def get_learn_page(request):
    return reverse("learn")


def get_user_groups(identity):
    """
    Returns a two tuple containing:
       selection of the users groups,
       boolean indicating if there are more
    """
    if identity.account is None:
        return [], False

    account = identity.account
    groups = account.get_ordered_groups()
    limit = 3
    groups = groups[0 : limit + 1]  # + 1 so we can see if we got more
    if len(groups) > limit:
        return groups[0:3], True
    else:
        return groups, False


@never_cache
def dashboard(request):
    identity = getattr(request, "identity", None)

    if identity is None:
        return HttpResponseRedirect(reverse("login"))

    if not identity.verse_statuses.exists():
        # The only possible thing is to choose some verses
        return HttpResponseRedirect(reverse("choose"))

    if request.method == "POST":
        get_catechism_id = lambda: int(request.POST["catechism_id"])
        if "continue_session" in request.POST:
            return HttpResponseRedirect(get_learn_page(request))

        if "learnbiblequeue" in request.POST:
            if "verse_set_id" in request.POST:
                vs_id = int(request.POST["verse_set_id"])
            else:
                vs_id = None
            return learn_set(request, identity.bible_verse_statuses_for_learning(vs_id), session.LearningType.LEARNING)
        if "reviewbiblequeue" in request.POST:
            return learn_set(request, identity.bible_verse_statuses_for_reviewing(), session.LearningType.REVISION)
        if "learncatechismqueue" in request.POST:
            return learn_set(
                request, identity.catechism_qas_for_learning(get_catechism_id()), session.LearningType.LEARNING
            )
        if "reviewcatechismqueue" in request.POST:
            return learn_set(
                request, identity.catechism_qas_for_reviewing(get_catechism_id()), session.LearningType.REVISION
            )
        if any(
            p in request.POST
            for p in [
                "learnpassage",
                "reviewpassage",
                "reviewpassagenextsection",
                "reviewpassagesection",
                "practisepassage",
                "practisepassagesection",
            ]
        ):

            # Some of these are sent via the verse_options.html template,
            # not from the dashboard.

            vs_id = int(request.POST["verse_set_id"])
            verse_set = VerseSet.objects.get(id=vs_id)

            if "uvs_id" in request.POST:
                # Triggered from 'verse_options.html'
                uvs_id = int(request.POST["uvs_id"])
                main_uvs = identity.verse_statuses.get(id=uvs_id)
                version_id = main_uvs.version_id

                uvss = identity.verse_statuses_for_passage(vs_id, version_id)
                if "reviewpassagesection" in request.POST or "practisepassagesection" in request.POST:
                    # Review/practise the specified section
                    uvss = main_uvs.get_section_verse_status_list(uvss)
            else:
                version_id = request.POST["version_id"]
                uvss = identity.verse_statuses_for_passage(vs_id, version_id)

            if "learnpassage" in request.POST:
                uvss = identity.slim_passage_for_reviewing(uvss, verse_set)
                return learn_set(request, uvss, session.LearningType.LEARNING)
            if "reviewpassage" in request.POST:
                uvss = identity.slim_passage_for_reviewing(uvss, verse_set)
                return learn_set(request, uvss, session.LearningType.REVISION)
            if "reviewpassagenextsection" in request.POST:
                uvss = identity.get_next_section(uvss, verse_set)
                return learn_set(request, uvss, session.LearningType.REVISION)
            if "reviewpassagesection" in request.POST:
                # Already filtered uvss above
                return learn_set(request, uvss, session.LearningType.REVISION)
            if "practisepassage" in request.POST:
                return learn_set(request, uvss, session.LearningType.PRACTICE)
            if "practisepassagesection" in request.POST:
                # Already filtered uvss above
                return learn_set(request, uvss, session.LearningType.PRACTICE)

        if "reviewverse" in request.POST:
            uvs = identity.verse_statuses.get(id=int(request.POST["uvs_id"]))
            return learn_set(
                request, [uvs], session.LearningType.REVISION if uvs.needs_testing else session.LearningType.PRACTICE
            )

        if "reviewcatechism" in request.POST:
            # This option reviews catechism questions even if they are not
            # due for revision yet.
            uvss = identity.get_all_tested_catechism_qas(get_catechism_id())
            return learn_set(request, uvss, session.LearningType.REVISION)

        if "clearbiblequeue" in request.POST:
            if "verse_set_id" in request.POST:
                vs_id = int(request.POST["verse_set_id"])
            else:
                vs_id = None
            identity.clear_bible_learning_queue(vs_id)
            return HttpResponseRedirect(reverse("dashboard"))
        if "clearcatechismqueue" in request.POST:
            identity.clear_catechism_learning_queue(get_catechism_id())
            return HttpResponseRedirect(reverse("dashboard"))
        if "cancelpassage" in request.POST:
            vs_id = int(request.POST["verse_set_id"])
            version_id = int(request.POST["version_id"])
            identity.cancel_passage(vs_id, version_id)
            return HttpResponseRedirect(reverse("dashboard"))

    groups, more_groups = get_user_groups(identity)

    passages_for_reviewing, passages_for_learning = identity.passages_for_reviewing_and_learning()
    # Bring passages that have already been started to the top,
    # and ones that have more to review above them.
    passages_for_learning.sort(key=lambda cvs: (cvs.tested_total == 0, -cvs.needs_review_total))

    ctx = {
        "learn_verses_queues": identity.bible_verse_statuses_for_learning_grouped(),
        "review_verses_queue": identity.bible_verse_statuses_for_reviewing(),
        "passages_for_learning": passages_for_learning,
        "passages_for_reviewing": passages_for_reviewing,
        "catechisms_for_learning": identity.catechisms_for_learning(),
        "catechisms_for_reviewing": identity.catechisms_for_reviewing(),
        "next_verse_due": identity.next_verse_due(),
        "title": t("dashboard-page-title"),
        "events": identity.get_dashboard_events(),
        "create_account_warning": identity.account is None,
        "groups": groups,
        "more_groups": more_groups,
        "url_after_logout": "/",
        "heatmap_stats_types": HeatmapStatsType.choices,
        "unfinished_session_first_uvs": session.unfinished_session_first_uvs(request),
        "use_dashboard_nav": True,
    }
    ctx.update(todays_stats(identity))
    return TemplateResponse(request, "learnscripture/dashboard.html", ctx)


def context_for_version_select(request):
    """
    Returns the context data needed to render a version select box
    """
    return {"bible_versions": bible_versions_for_request(request)}


def context_for_quick_find(request):
    """
    Returns the context data needed to render a quick find box
    """
    version = default_bible_version_for_request(request)
    language_codes = [lang.code for lang in LANGUAGES] + [LANGUAGE_CODE_INTERNAL]

    bible_books = [{lc: get_bible_book_name(lc, i) for lc in language_codes} for i in range(0, BIBLE_BOOK_COUNT)]
    d = {
        "bible_books": bible_books,
        "default_bible_version": version,
        "language_codes": language_codes,
        "current_language_code": version.language_code,
    }
    d.update(context_for_version_select(request))
    return d


def default_bible_version_for_request(request):
    version = None
    if has_preferences(request):
        version = request.identity.default_bible_version
    if version is None:
        if request.LANGUAGE_CODE != settings.LANGUAGE_CODE:
            version = TextVersion.objects.filter(language_code=request.LANGUAGE_CODE).order_by("id").first()
    if version is not None:
        return version
    return get_default_bible_version()


# No 'require_preferences' or 'require_identity' so that bots can browse this
# page and the linked pages unhindered, for SEO.


@for_htmx(if_target="id-choose-verseset-results", template="learnscripture/choose_verseset_inc.html")
@for_htmx(if_target="id-more-results-container", template="learnscripture/choose_verseset_results_inc.html")
def choose(request):
    """
    Choose a verse or verse set
    """
    default_bible_version = default_bible_version_for_request(request)
    verse_sets = verse_sets_visible_for_request(request)

    # Searching for verse sets is done via this view. But looking up individual
    # verses is done by AJAX, so is missing here.

    active_section = None
    verseset_search_form = VerseSetSearchForm.from_request_data(
        request.GET, defaults={"language_code": request.LANGUAGE_CODE}
    )
    if any(k in request.GET for k in VerseSetSearchForm.base_fields.keys()):
        active_section = "verseset"
    if "from_item" in request.GET:
        active_section = "verseset"

    ctx = {
        "title": t("choose-page-title"),
        "verseset_search_form": verseset_search_form,
    }

    verse_sets = verse_sets.order_by("name").prefetch_related("verse_choices")

    query = verseset_search_form.cleaned_data["query"].strip()
    language_code = verseset_search_form.cleaned_data["language_code"]

    query_language_codes = (
        settings.LANGUAGE_CODES
        if language_code == FILTER_LANGUAGES_ALL
        else list(
            {
                # People will typically type in 'interface language' (request.LANGUAGE_CODES),
                # and if that doesn't find anything, they may just switch the language filter
                # to another language, perhaps English. They will expect what they typed
                # before to be still valid.
                language_code,
                request.LANGUAGE_CODE,
            }
        )
    )
    verse_sets = verse_sets.search(query_language_codes, query)

    if language_code != FILTER_LANGUAGES_ALL:
        ctx["verseset_language_code"] = language_code
    else:
        ctx["verseset_language_code"] = default_bible_version.language_code

    set_type = verseset_search_form.cleaned_data["set_type"]
    if set_type != VERSE_SET_TYPE_ALL:
        verse_sets = verse_sets.filter(set_type=set_type)

    order = verseset_search_form.cleaned_data["order"]
    if order == VERSE_SET_ORDER_POPULARITY:
        verse_sets = verse_sets.order_by("-popularity", "-id")
    elif order == VERSE_SET_ORDER_AGE:
        verse_sets = verse_sets.order_by("-date_added", "-id")

    if set_type != VerseSetType.SELECTION and query != "":
        # Does the query look like a Bible reference?
        try:
            parsed_ref = parse_unvalidated_localized_reference(
                language_code if language_code != FILTER_LANGUAGES_ALL else request.LANGUAGE_CODE,
                query,
                allow_whole_book=False,
                allow_whole_chapter=True,
            )
        except InvalidVerseReference:
            parsed_ref = None

        if parsed_ref is not None:
            # TODO It would also be nice to detect the case where
            # is no complete match for the searched passage.
            if len(verse_sets) == 0:
                ctx["create_passage_set_prompt"] = {
                    "internal_reference": parsed_ref.to_internal().canonical_form(),
                    "localized_reference": parsed_ref.canonical_form(),
                }

    PAGE_SIZE = 10

    if active_section:
        ctx["active_section"] = active_section

    ctx["results"] = get_paged_results(verse_sets, request, PAGE_SIZE)
    ctx["default_bible_version"] = default_bible_version

    ctx.update(context_for_quick_find(request))

    return TemplateResponse(request, "learnscripture/choose.html", ctx)


@require_preferences
@require_POST
def handle_choose_set(request):
    identity = request.identity
    default_bible_version = default_bible_version_for_request(request)
    verse_sets = verse_sets_visible_for_request(request)
    version = None
    try:
        version = TextVersion.objects.get(slug=request.POST["version_slug"])
    except (KeyError, TextVersion.DoesNotExist):
        version = default_bible_version

    try:
        vs_id = int(request.POST["verseset_id"])
        vs = verse_sets.prefetch_related("verse_choices").get(id=vs_id)
    except (KeyError, ValueError, VerseSet.DoesNotExist):
        return HttpResponseRedirect(reverse("choose"))
    return learn_set(request, identity.add_verse_set(vs, version=version), session.LearningType.LEARNING)


@require_preferences
@require_POST
def handle_choose_verse(request):
    identity = request.identity
    default_bible_version = default_bible_version_for_request(request)
    try:
        version = TextVersion.objects.get(slug=request.POST["version_slug"])
    except (KeyError, TextVersion.DoesNotExist):
        version = default_bible_version

    try:
        ref = request.POST["localized_reference"]
    except KeyError:
        return HttpResponseRedirect(reverse("choose"))

    try:
        version.get_verse_list(ref, max_length=MAX_VERSES_FOR_SINGLE_CHOICE)
    except InvalidVerseReference:
        # Ignore
        return HttpResponseRedirect(reverse("choose"))
    return learn_set(request, [identity.add_verse_choice(ref, version=version)], session.LearningType.LEARNING)


def view_catechism_list(request):
    if request.method == "POST":
        if not has_preferences(request):
            # Shouldn't get here if UI preferences javascript is working right.
            return redirect_via_prefs(request)
        try:
            catechism = TextVersion.objects.get(id=int(request.POST["catechism_id"]))
        except (KeyError, ValueError, TextVersion.DoesNotExist):
            raise Http404
        return learn_set(request, request.identity.add_catechism(catechism), session.LearningType.LEARNING)

    ctx = {
        "catechisms": TextVersion.objects.catechisms(),
        "title": t("catechisms-page-title"),
    }
    return TemplateResponse(request, "learnscripture/catechisms.html", ctx)


def view_catechism(request, slug):
    try:
        catechism = TextVersion.objects.get(slug=slug)
    except TextVersion.DoesNotExist:
        raise Http404

    ctx = {
        "title": catechism.full_name,
        "catechism": catechism,
        "questions": catechism.qapairs.order_by("order"),
        "learners": catechism.get_learners(),
        "include_referral_links": True,
    }

    return TemplateResponse(request, "learnscripture/view_catechism.html", ctx)


def verse_options(request):
    """
    Returns a page fragment showing a list of learning options for
    the verse in request.GET['ref']
    """
    # This view is called from the 'progress' page where the list of verses
    # being learned by a user is shown.
    if not hasattr(request, "identity"):
        return HttpResponse("Error: not logged in")
    identity = request.identity
    ref = request.GET["ref"]
    version_slug = request.GET["version_slug"]
    uvss = identity.verse_statuses_for_ref_and_version(ref, version_slug)
    if len(uvss) == 0:
        return HttpResponse("Error: not learning this verse")

    # FIXME: move more of this logic into Identity model, ideally.

    # Different options:
    # - could *review*
    # - could *practice*, if revision not due
    # - for verses in passage sets, could learn section or passage

    # In this context, the different UserVerseStatus objects need to be treated
    # differently, because there are different actions if the verse is part of a
    # passage verse set. However, two different UVS not attached to a passage
    # verse set are equivalent.
    uvss = _reduce_uvs_set_for_verse(uvss)
    # UVS not in passage goes first
    uvss.sort(key=lambda uvs: uvs.is_in_passage())
    return TemplateResponse(
        request,
        "learnscripture/verse_options.html",
        {
            "uvs_list": uvss,
        },
    )


def _reduce_uvs_set_for_verse(uvss):
    # Filters out multiple instances of non-passage UVSs
    retval = []
    non_passage_seen = False
    for uvs in uvss:
        if not uvs.is_in_passage():
            if non_passage_seen:
                continue
            else:
                non_passage_seen = True
        retval.append(uvs)
    return retval


def get_default_bible_version():
    # Use NET as default version because:
    # - they let us use their version without royalties
    # - it is a modern readable version.
    return TextVersion.objects.get(slug="NET")


def verse_sets_visible_for_request(request):
    return VerseSet.objects.visible_for_account(account_from_request(request))


def get_verse_set_verse_list(version, verse_set):
    language_code = version.language_code

    verse_choices = list(verse_set.verse_choices.all().order_by("set_order"))
    all_localized_references = [
        localize_internal_reference(language_code, vc.internal_reference) for vc in verse_choices
    ]
    verse_list = version.get_verse_list_by_localized_reference_bulk(all_localized_references)
    if verse_set.is_passage:
        verse_list = add_passage_breaks(verse_list, verse_set.breaks)

    return verse_list


def view_verse_set(request, slug):
    verse_set = get_object_or_404(verse_sets_visible_for_request(request), slug=slug)
    ctx = {"include_referral_links": verse_set.public}

    try:
        version = bible_versions_for_request(request).get(slug=request.GET["version"])
    except (KeyError, TextVersion.DoesNotExist):
        version = default_bible_version_for_request(request)

    verse_list = get_verse_set_verse_list(version, verse_set)
    all_localized_references = [v.localized_reference for v in verse_list]

    if hasattr(request, "identity") and request.identity.can_edit_verse_set(verse_set):
        if verse_set.is_selection and is_continuous_set(verse_list):
            ctx["show_convert_to_passage"] = True

            if request.method == "POST":
                if "convert_to_passage_set" in request.POST:
                    verse_set.set_type = VerseSetType.PASSAGE
                    verse_set.save()
                    messages.info(request, t("versesets-converted-to-passage"))
                    ctx["show_convert_to_passage"] = False

    if request.method == "POST":
        if "drop" in request.POST and hasattr(request, "identity"):
            refs_to_drop = request.identity.which_in_learning_queue(all_localized_references, version)
            request.identity.cancel_learning(refs_to_drop, version.slug)
            messages.info(request, t("versesets-dropped-verses", dict(count=len(refs_to_drop))))

    if hasattr(request, "identity"):
        ctx["can_edit"] = request.identity.can_edit_verse_set(verse_set)
        verses_started = request.identity.which_verses_started(all_localized_references, version)
        ctx["started_count"] = len(verses_started)

        if verse_set.is_selection:
            ctx["in_queue"] = len(request.identity.which_in_learning_queue(all_localized_references, version))
        else:
            ctx["in_queue"] = 0
    else:
        ctx["can_edit"] = False
        ctx["started_count"] = 0
        ctx["in_queue"] = 0

    ctx["verse_set"] = verse_set
    ctx["verse_list"] = verse_list
    ctx["version"] = version
    ctx["title"] = t("versesets-view-set-page-title", dict(name=verse_set.smart_name(version.language_code)))
    ctx["include_referral_links"] = True

    ctx.update(context_for_version_select(request))
    return TemplateResponse(request, "learnscripture/single_verse_set.html", ctx)


def add_passage_breaks(verse_list, breaks):
    """
    Decorates verse list (UserVerseStatus or VerseChoice) with `break_here` attributes.
    """
    retval = []
    sections = get_passage_sections(verse_list, breaks)
    for i, section in enumerate(sections):
        for j, v in enumerate(section):
            # need break at beginning of every section except first
            v.break_here = j == 0 and i != 0
            retval.append(v)
    return retval


@require_preferences
def create_selection_set(request, slug=None):
    return create_or_edit_set(request, set_type=VerseSetType.SELECTION, slug=slug)


@require_preferences
def create_passage_set(request, slug=None):
    return create_or_edit_set(request, set_type=VerseSetType.PASSAGE, slug=slug)


@require_preferences
def edit_set(request, slug=None):
    return create_or_edit_set(request, slug=slug)


@require_account_with_redirect
def create_or_edit_set(request, set_type=None, slug=None):
    form_class = VerseSetForm

    version = request.identity.default_bible_version
    language_code = version.language_code

    if slug is not None:
        verse_set = get_object_or_404(request.identity.account.verse_sets_editable.filter(slug=slug))
        set_type = verse_set.set_type
        mode = "edit"
    else:
        verse_set = None
        mode = "create"

    title = (
        t("versesets-edit-set-page-title")
        if verse_set is not None
        else t("versesets-create-selection-page-title")
        if set_type == VerseSetType.SELECTION
        else t("versesets-create-passage-page-title")
    )

    ctx = {}

    if request.method == "POST":
        orig_verse_set_public = False if verse_set is None else verse_set.public

        form = form_class(request.POST, instance=verse_set)
        if set_type == VerseSetType.SELECTION:
            internal_parsed_reference_list = [
                parse_validated_internal_reference(i)
                for i in request.POST.get("internal_reference_list", "").split("|")
                if i
            ]
            breaks = ""
        else:
            passage_id = request.POST.get("passage_id", "")
            try:
                internal_parsed_reference_list = verse_set_passage_id_to_parsed_ref(passage_id).to_list()
            except InvalidVerseReference:
                internal_parsed_reference_list = []
            breaks = normalize_break_list(request.POST.get("break_list", ""))
            # If all have a 'break' applied, (excluding first, which never has
            # one) then the user clearly doesn't understand the concept of
            # section breaks:
            tmp_verse_list = add_passage_breaks(
                [VerseChoice(internal_reference=r.canonical_form()) for r in internal_parsed_reference_list], breaks
            )
            if all(v.break_here for v in tmp_verse_list[1:]):
                breaks = ""

        form_is_valid = form.is_valid()
        if len(internal_parsed_reference_list) == 0:
            form.errors.setdefault("__all__", form.error_class()).append(t("versesets-no-verses-error"))
            form_is_valid = False

        if form_is_valid:
            verse_set = form.save(commit=False)
            verse_set.set_type = set_type
            if verse_set.created_by_id is None:
                verse_set.created_by = request.identity.account
            verse_set.breaks = breaks

            if orig_verse_set_public:
                # Can't undo:
                verse_set.public = True
            verse_set.save()
            verse_set.set_verse_choices([ref.canonical_form() for ref in internal_parsed_reference_list])

            # if user just made it public or it is a new public verse set
            if verse_set.public and (not orig_verse_set_public or mode == "create"):
                public_verse_set_created.send(sender=verse_set)

            messages.info(request, t("versesets-set-saved", dict(name=verse_set.name)))
            return HttpResponseRedirect(reverse("view_verse_set", kwargs=dict(slug=verse_set.slug)))

    else:
        # GET request - initial view
        initial = {}
        breaks = ""
        internal_parsed_reference_list = []
        if verse_set is not None:
            breaks = verse_set.breaks
            internal_parsed_reference_list = [
                parse_validated_internal_reference(vc.internal_reference) for vc in verse_set.verse_choices.all()
            ]
        else:
            if set_type == VerseSetType.PASSAGE and "ref" in request.GET:
                # Shortcut link for creating a passage verse set
                try:
                    parsed_ref = parse_validated_internal_reference(request.GET["ref"])
                except InvalidVerseReference:
                    parsed_ref = None
                if parsed_ref is not None:
                    localized_reference = parsed_ref.translate_to(language_code).canonical_form()
                    initial["name"] = localized_reference
                    ctx["initial_localized_reference"] = localized_reference
            if form_class is VerseSetForm:
                initial["language_code"] = language_code

        form = form_class(instance=verse_set, initial=initial)

    # Fetch verses to be displayed:
    localized_references = [
        ref.translate_to(version.language_code).canonical_form() for ref in internal_parsed_reference_list
    ]
    verse_list = version.get_verse_list_by_localized_reference_bulk(localized_references)
    if set_type == VerseSetType.PASSAGE:
        verse_list = add_passage_breaks(verse_list, breaks)

    ctx.update(
        {
            "verses": verse_list,
            "breaks": breaks,
            "verse_set": verse_set,
            "new_verse_set": verse_set is None,
            "verse_set_form": form,
            "title": title,
            "set_type": set_type,
        }
    )
    ctx.update(context_for_quick_find(request))

    return TemplateResponse(request, "learnscripture/create_set.html", ctx)


def normalize_break_list(breaks):
    break_list = parse_break_list(breaks)
    break_list = [r.get_start() for r in break_list]
    return ",".join(r.canonical_form() for r in break_list)


def get_hellbanned_mode(request):
    account = account_from_request(request)
    if account is None:
        # Guests see the site as normal users
        return False
    else:
        # hellbanned users see the hellbanned version of reality
        return account.is_hellbanned


@for_htmx(if_target="id-follow-form", template="learnscripture/follow_form_inc.html")
def user_stats(request, username):
    viewer = account_from_request(request)
    account = get_object_or_404(
        Account.objects.visible_for_account(viewer).select_related("total_score", "identity"), username=username
    )
    if viewer is not None and viewer == account:
        account_groups = account.groups.order_by("name")
    else:
        account_groups = account.groups.public().order_by("name")
    viewer_visible_groups = Group.objects.visible_for_account(viewer).filter(id__in=[g.id for g in account_groups])

    if request.method == "POST" and viewer is not None:
        if "follow" in request.POST:
            viewer.follow_user(account)
        if "unfollow" in request.POST:
            viewer.unfollow_user(account)

    one_week_ago = timezone.now() - timedelta(7)
    ctx = {
        "account": account,
        "title": account.username,
        "awards": account.visible_awards(),
        "include_referral_links": True,
        "events": _user_events(account, viewer)[:USER_EVENTS_SHORT_CUTOFF],
        "verses_started_all_time": account.identity.verses_started_count(),
        "verses_started_this_week": account.identity.verses_started_count(started_since=one_week_ago),
        "verses_finished_all_time": account.identity.verses_finished_count(),
        "verses_finished_this_week": account.identity.verses_finished_count(finished_since=one_week_ago),
        "verse_sets_created_all_time": account.verse_sets_created.count(),
        "verse_sets_created_this_week": account.verse_sets_created.filter(date_added__gte=one_week_ago).count(),
        "groups": viewer_visible_groups,
    }

    if viewer is not None:
        ctx["viewer_is_following"] = viewer.is_following(account)

    return TemplateResponse(request, "learnscripture/user_stats.html", ctx)


@require_identity
@for_htmx(if_target="id-user-verses-results", template="learnscripture/user_verses_inc.html")
@for_htmx(if_target="id-more-results-container", template="learnscripture/user_verses_table_body_inc.html")
def user_verses(request):
    identity = request.identity

    # verse_statuses_started contains dupes, we do deduplication in the
    # template.
    verses = identity.verse_statuses_started().select_related("version")

    filter_form = UserVersesFilterForm.from_request_data(request.GET)
    text_type = filter_form.cleaned_data["text_type"]
    verses = verses.filter(version__text_type=text_type)
    sort_order = filter_form.cleaned_data["order"]
    query = filter_form.cleaned_data["query"].strip()

    if query != "":
        if text_type == TextType.BIBLE:
            invalid = False
            try:
                # TODO - this doesn't work nicely if you are learning more than
                # one language - you can only search in the language that is
                # your default language.
                parsed_ref = parse_unvalidated_localized_reference(
                    request.identity.default_language_code,
                    query,
                    allow_whole_book=True,
                    allow_whole_chapter=True,
                )
            except InvalidVerseReference:
                invalid = True

            if invalid or parsed_ref is None:
                # To make it clear we didn't match anything
                verses = verses.none()
            else:
                verses = verses.search_by_parsed_ref(parsed_ref)
        else:
            # TextType.CATECHISM
            verses = verses.filter(localized_reference__iexact=query)

    PAGE_SIZE = 20

    if sort_order == USER_VERSES_ORDER_WEAKEST:
        verses = verses.order_by("strength", "text_order")
    elif sort_order == USER_VERSES_ORDER_STRONGEST:
        verses = verses.order_by("-strength", "text_order")
    else:
        # Text order
        if text_type == TextType.CATECHISM:
            # It's more useful to group catechisms together
            verses = verses.order_by("version__slug", "text_order")
        else:
            verses = verses.order_by("text_order", "version__slug")

    ctx = {
        "title": t("user-verses-page-title"),
        "filter_form": filter_form,
        "results": get_paged_results(verses, request, PAGE_SIZE),
        "bible": text_type == TextType.BIBLE,
        "catechism": text_type == TextType.CATECHISM,
    }

    return TemplateResponse(request, "learnscripture/user_verses.html", ctx)


@require_identity
def user_verse_sets(request):
    identity = request.identity
    ctx = {
        "title": t("user-verse-sets-page-title"),
        "chosen_verse_sets": identity.verse_sets_chosen(),
    }
    if identity.account is not None:
        ctx["verse_sets_created"] = identity.account.verse_sets_created.all().order_by("name")

    return TemplateResponse(request, "learnscripture/user_verse_sets.html", ctx)


# Password reset for Accounts:
#
# We can re-use a large amount of django.contrib.auth functionality due to same
# interface between Account and User. Some things need customizing/replacing.
#
# Also, we do the main password_reset via AJAX, from the same form as the login
# form.
def password_reset_done(request):
    return TemplateResponse(
        request,
        "learnscripture/password_reset_done.html",
        {
            "title": t("accounts-password-reset-start-page-title"),
        },
    )


def password_reset_complete(request):
    return TemplateResponse(
        request,
        "learnscripture/password_reset_complete.html",
        {
            "title": t("accounts-password-reset-complete-page-title"),
        },
    )


# Copy and paste from django.contrib.auth.views, followed by customizations.
@sensitive_post_parameters()
@never_cache
def password_reset_confirm(request, uidb64=None, token=None):
    """
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    token_generator = default_token_generator
    set_password_form = AccountSetPasswordForm
    assert uidb64 is not None and token is not None  # checked by URLconf
    post_reset_redirect = reverse("password_reset_complete")
    try:
        uid_int = urlsafe_base64_decode(uidb64)
        user = Account.objects.get(id=uid_int)
    except (ValueError, Account.DoesNotExist):
        user = None

    if user is not None and token_generator.check_token(user, token):
        validlink = True
        if request.method == "POST":
            form = set_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(post_reset_redirect)
        else:
            form = set_password_form(None)
    else:
        validlink = False
        form = None
    ctx = {
        "form": form,
        "validlink": validlink,
        "title": t("accounts-password-reset-page-title"),
    }
    return TemplateResponse(request, "learnscripture/password_reset_confirm.html", ctx)


@require_account
def password_change(request):
    account = account_from_request(request)
    password_change_form = AccountPasswordChangeForm
    template_name = "learnscripture/password_change_form.html"

    if request.method == "POST":
        form = password_change_form(user=account, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("learnscripture_password_change_done"))
    else:
        form = password_change_form(user=account)
    ctx = {
        "form": form,
        "title": t("accounts-password-change-page-title"),
    }

    return TemplateResponse(request, template_name, ctx)


def password_change_done(request):
    return TemplateResponse(request, "learnscripture/password_change_done.html", {})


def csrf_failure(request, reason=""):
    """
    Default view used when request fails CSRF protection
    """
    from django.middleware.csrf import REASON_NO_CSRF_COOKIE

    resp = TemplateResponse(request, "csrf_failure.html", {"no_csrf_cookie": reason == REASON_NO_CSRF_COOKIE})
    resp.status_code = 403
    return resp


def offline(request):
    return TemplateResponse(request, "offline.html", {})


@require_account_with_redirect
def account_details(request):
    if request.method == "POST":
        form = AccountDetailsForm(request.POST, instance=request.identity.account)
        if form.is_valid():
            form.save()
            messages.info(request, t("accounts-details-updated"))
            return HttpResponseRedirect(reverse("account_details"))
    else:
        form = AccountDetailsForm(instance=request.identity.account)

    return TemplateResponse(
        request,
        "learnscripture/account_details.html",
        {
            "form": form,
            "title": t("accounts-details-page-title"),
            "url_after_logout": "/",
        },
    )


def date_to_js_ts(d):
    """
    Converts a date object to the timestamp required by the flot library
    """
    return int(d.strftime("%s")) * 1000


def stats(request):
    now = timezone.now()
    period = int(request.GET.get("period", 180))
    start = now - timedelta(days=period)
    stats_raw = get_account_stats(start, now)

    # Build the stats dict template is expecting (see stats.html)
    stats_dict = {}
    for stat in ["new_accounts", "active_accounts", "verses_started", "verses_tested"]:
        stats_dict[stat] = []
        for account_stat in stats_raw:
            stats_dict[stat].append((date_to_js_ts(account_stat.date), getattr(account_stat, stat)))

    return TemplateResponse(
        request,
        "learnscripture/stats.html",
        {
            "title": "Stats",
            "stats": stats_dict,
        },
    )


def donation_paypal_dict(account, url_start):
    return {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "item_name": t("donations-paypal-title"),
        "invoice": f"account-{account.id}-{timezone.now()}",  # We don't need this, but must be unique
        "notify_url": f"{url_start}{reverse('paypal-ipn')}",
        "return_url": f"{url_start}{reverse('pay_done')}",
        "cancel_return": f"{url_start}{reverse('pay_cancelled')}",
        "custom": sign_payment_info(dict(account=account.id)),
        "currency_code": "GBP",
        "no_note": "1",
        "no_shipping": "1",
    }


def paypal_url_start_for_request(request):
    """
    Returns the start of the URLs to be passed to PayPal
    """
    domain = Site.objects.get_current().domain
    if getattr(settings, "STAGING", False):
        # Sometimes for staging site, we have a DB that has been dumped from production,
        # but needs Site object updated. Stop here, or payment testing won't work.
        assert domain.startswith("staging.")
    protocol = "https" if request.is_secure() else "http"
    return f"{protocol}://{domain}"


def donate(request):
    ctx = {"title": t("donations-page-title")}
    account = account_from_request(request)
    if account is not None:
        url_start = paypal_url_start_for_request(request)
        paypal_dict = donation_paypal_dict(account, url_start)
        form = PayPalPaymentsForm(initial=paypal_dict)
        ctx.update(
            {
                "LIVEBOX": settings.LIVEBOX,
                "paypal_form": form,
            }
        )

    return TemplateResponse(request, "learnscripture/donate.html", ctx)


@csrf_exempt
def pay_done(request):
    identity = getattr(request, "identity", None)
    if identity is not None:
        if identity.account is not None:
            return HttpResponseRedirect(reverse("dashboard"))

    return TemplateResponse(request, "learnscripture/pay_done.html", {"title": t("donations-completed-page-title")})


@csrf_exempt
def pay_cancelled(request):
    return TemplateResponse(
        request, "learnscripture/pay_cancelled.html", {"title": t("donations-cancelled-page-title")}
    )


def referral_program(request):
    account = account_from_request(request)
    if account is not None:
        referral_link = account.make_referral_link(f"https://{Site.objects.get_current().domain}/")
    else:
        referral_link = None
    return TemplateResponse(
        request,
        "learnscripture/referral_program.html",
        {
            "title": t("referrals-page-title"),
            "referral_link": referral_link,
            "include_referral_links": True,
        },
    )


def awards(request):
    award_classes = [AWARD_LOGIC_CLASSES[t] for t in AwardType.values]
    awards = [cls(level=AnyLevel) for cls in award_classes if not cls.removed]
    return TemplateResponse(
        request,
        "learnscripture/awards.html",
        {
            "title": t("awards-page-title"),
            "awards": awards,
        },
    )


def award(request, slug):
    award_name = slug.replace("-", "_").upper()
    try:
        award_type = AwardType(award_name)
    except ValueError:
        raise Http404
    if not Award.objects.filter(award_type=award_type).exists():
        raise Http404
    award_class = AWARD_LOGIC_CLASSES[award_type]
    if award_class.removed:
        return missing(request, t("awards-removed", dict(name=award_class.title)), status_code=410)
    award = award_class(level=AnyLevel)

    levels = []

    hellbanned_mode = get_hellbanned_mode(request)
    for level in range(award.max_level, 0, -1):
        awards = Award.objects.filter(award_type=award_type, account__is_active=True, level=level)
        if not hellbanned_mode:
            awards = awards.exclude(account__is_hellbanned=True)

        receivers_count = awards.count()
        if receivers_count > 0:
            sample_usernames = list(awards.order_by("-created").values_list("account__username", flat=True)[0:5])
            sample_award = Award(award_type=award_type, level=level)
            levels.append((level, receivers_count, sample_usernames, sample_award))

    account_top_award = None
    account = account_from_request(request)
    if account is not None:
        try:
            account_top_award = account.awards.filter(award_type=award_type).order_by("-level")[0]
        except IndexError:
            pass

    return TemplateResponse(
        request,
        "learnscripture/award.html",
        {
            "title": t("awards-award-page-title", dict(name=award.short_description())),
            "award": award,
            "levels": levels,
            "account_top_award": account_top_award,
        },
    )


def groups_visible_for_request(request):
    return Group.objects.visible_for_account(account_from_request(request))


def groups_editable_for_request(request):
    return Group.objects.editable_for_account(account_from_request(request))


@for_htmx(if_target="id-groups-results", template="learnscripture/groups_inc.html")
@for_htmx(if_target="id-more-results-container", template="learnscripture/groups_results_inc.html")
def group_list(request):
    account = account_from_request(request)
    groups = Group.objects.visible_for_account(account).order_by("name")
    filter_form = GroupFilterForm.from_request_data(
        request.GET,
        defaults={"language_code": request.LANGUAGE_CODE},
    )
    query = filter_form.cleaned_data["query"].strip()
    if query:
        groups = groups.search(query)
    else:
        groups = groups.none()
    language_code = filter_form.cleaned_data["language_code"]
    if language_code != FILTER_LANGUAGES_ALL:
        groups = groups.filter(language_code=language_code)

    return TemplateResponse(
        request,
        "learnscripture/groups.html",
        {
            "title": t("groups-page-title"),
            "results": get_paged_results(groups, request, 10),
            "filter_form": filter_form,
            "query": query,
        },
    )


def group_by_slug(request, slug):
    groups = groups_visible_for_request(request)
    return get_object_or_404(groups, slug=slug)


def group(request, slug):
    group = group_by_slug(request, slug)
    account = account_from_request(request)

    if request.method == "POST":
        if account is None:
            return HttpResponseRedirect(build_signup_url(request))

        if "leave" in request.POST:
            group.remove_user(account)
            messages.info(request, t("groups-removed-from-group", dict(name=group.name)))
            return HttpResponseRedirect(request.get_full_path())
        if "join" in request.POST:
            if group.can_join(account):
                group.add_user(account)
                messages.info(request, t("groups-added-to-group", dict(name=group.name)))
            return HttpResponseRedirect(request.get_full_path())

    if account is not None:
        in_group = group.members.filter(id=account.id).exists()
    else:
        in_group = False

    return TemplateResponse(
        request,
        "learnscripture/group.html",
        {
            "title": t("groups-group-page-title", dict(name=group.name)),
            "group": group,
            "in_group": in_group,
            "can_join": group.can_join(account),
            "can_edit": group.can_edit(account),
            "include_referral_links": True,
            "comments": group.comments_visible_for_account(account).order_by("-created")[:GROUP_COMMENTS_SHORT_CUTOFF],
        },
    )


@for_htmx(if_target="id-group-wall-comments", template="learnscripture/group_wall_comments_inc.html")
@for_htmx(if_target="id-more-results-container", template="learnscripture/group_wall_comments_results_inc.html")
def group_wall(request, slug):
    account = account_from_request(request)
    group = group_by_slug(request, slug)

    # TODO: respond to 'comment' query param and ensure we include the right
    # page of comments.
    try:
        selected_comment_id = int(request.GET["comment"])
    except (KeyError, ValueError):
        selected_comment_id = None

    comments = group.comments_visible_for_account(account)
    filter_form = GroupWallFilterForm.from_request_data(request.GET)
    sort_order = filter_form.cleaned_data["order"]
    if sort_order == GROUP_WALL_ORDER_OLDEST_FIRST:
        comments = comments.order_by("created")
    else:
        comments = comments.order_by("-created")

    ctx = {
        "title": t("groups-wall-page-title", dict(name=group.name)),
        "filter_form": filter_form,
        "group": group,
        "results": get_paged_results(comments, request, GROUP_COMMENTS_PAGINATE_BY),
        "sort_order": sort_order,
        "selected_comment_id": selected_comment_id,
    }
    return TemplateResponse(request, "learnscripture/group_wall.html", ctx)


@for_htmx(
    if_target="id-leaderboard-results-table-body", template="learnscripture/leaderboard_results_table_body_inc.html"
)
@for_htmx(if_target="id-more-results-container", template="learnscripture/leaderboard_results_table_body_inc.html")
def group_leaderboard(request, slug):
    PAGE_SIZE = 30
    from_item = get_request_from_item(request)
    leaderboard_filter_form = LeaderboardFilterForm.from_request_data(request.GET)
    thisweek = leaderboard_filter_form.cleaned_data["when"] == LEADERBOARD_WHEN_THIS_WEEK

    if thisweek:
        cutoff = timezone.now() - timedelta(7)
    else:
        cutoff = None

    group = group_by_slug(request, slug)

    hellbanned_mode = get_hellbanned_mode(request)
    if thisweek:
        accounts = get_leaderboard_since(cutoff, hellbanned_mode, from_item, PAGE_SIZE, group=group)
    else:
        accounts = get_all_time_leaderboard(hellbanned_mode, from_item, PAGE_SIZE, group=group)

    # Now decorate these accounts with additional info from additional queries
    account_ids = [a["account_id"] for a in accounts]
    # identities and account info
    identities = Identity.objects.filter(account__id__in=account_ids).select_related("account")
    identity_ids = [i.id for i in identities]
    identity_dict = {i.account_id: i for i in identities}

    # Counts of verses learned
    verse_counts = get_verses_started_counts(identity_ids, cutoff)

    for account_dict in accounts:
        identity = identity_dict[account_dict["account_id"]]
        account_dict["num_verses"] = verse_counts[identity.id]
        account_dict["username"] = identity.account.username

    last_item = from_item + PAGE_SIZE
    shown_count = min(last_item, from_item + len(accounts))

    ctx = {
        "include_referral_links": True,
        "thisweek": thisweek,
        # We can't use get_paged_results for 'results' because it doesn't use a
        # normal queryset. Could possibly fix this by rewriting leaderboard
        # queries with Window functions introduced in Django 2.0?
        "results": Page(
            items=accounts,
            from_item=from_item,
            shown_count=shown_count,
            more=len(accounts) == PAGE_SIZE,  # There *might* be more in this case, otherwise definitely not
            more_link=(
                furl.furl(request.get_full_path())
                .remove(query=["from_item"])
                .add(query_params={"from_item": last_item})
            ),
        ),
        "group": group,
        "title": t("groups-leaderboard-page-title", dict(name=group.name)),
        "leaderboard_filter_form": leaderboard_filter_form,
    }
    return TemplateResponse(request, "learnscripture/leaderboard.html", ctx)


@require_account_with_redirect
def create_group(request):
    return _create_or_edit_group(request)


@require_account_with_redirect
def edit_group(request, slug):
    group = get_object_or_404(groups_editable_for_request(request).filter(slug=slug))
    return _create_or_edit_group(request, group=group)


def _create_or_edit_group(request, group=None):
    account = account_from_request(request)
    if group is not None:
        title = t("groups-edit-page-title", dict(name=group.name))
        initial = {"invited_users": group.invited_users()}
    else:
        title = t("groups-create-page-title")
        initial = {"language_code": account.default_language_code}

    was_public = group.public if group is not None else False

    if request.method == "POST":
        form = EditGroupForm(request.POST, instance=group, initial=initial)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = account
            if was_public:
                group.public = True
            group.save()

            if not was_public and group.public:
                public_group_created.send(sender=group)

            # Handle invitations
            group.set_invitation_list(form.cleaned_data["invited_users"])
            messages.info(request, t("groups-group-created"))
            return HttpResponseRedirect(reverse("group", args=(group.slug,)))
    else:
        form = EditGroupForm(instance=group, initial=initial)

    return TemplateResponse(
        request,
        "learnscripture/edit_group.html",
        {
            "title": title,
            "group": group,
            "form": form,
        },
    )


def group_select_list(request):
    account = account_from_request(request)
    groups = list(Group.objects.visible_for_account(account))
    if account is not None:
        own_groups = set(account.groups.all())
        for g in groups:
            g.is_member = g in own_groups
        groups.sort(key=lambda g: not g.is_member)
    return TemplateResponse(
        request,
        "learnscripture/group_select_list.html",
        {
            "groups": groups,
        },
    )


def terms_of_service(request):
    return TemplateResponse(
        request,
        "learnscripture/terms_of_service.html",
        {
            "title": t("terms-of-service-page-title"),
        },
    )


def contact(request):
    account = account_from_request(request)
    if account is not None:
        email_body = f"Account: {account.username} - {account.first_name} {account.last_name}\n\n\n"
    else:
        email_body = ""
    return TemplateResponse(
        request,
        "learnscripture/contact.html",
        {
            "title": t("contact-form-page-title"),
            "email_body": urllib.parse.quote(email_body),
        },
    )


@for_htmx(template="learnscripture/activity_stream_results_inc.html")
def activity_stream(request):
    viewer = account_from_request(request)
    events = Event.objects.for_activity_stream(viewer=viewer).prefetch_related("comments", "comments__author")
    return TemplateResponse(
        request,
        "learnscripture/activity_stream.html",
        {
            "results": get_paged_results(events, request, 40),
            "title": t("activity-page-title"),
            "following_ids": [] if viewer is None else [a.id for a in viewer.following.all()],
        },
    )


def _user_events(for_account, viewer):
    return Event.objects.for_activity_stream(
        viewer=viewer,
        event_by=for_account,
    ).prefetch_related("comments", "comments__author")


@for_htmx(template="learnscripture/activity_stream_results_inc.html")
def user_activity_stream(request, username):
    account = get_object_or_404(Account.objects.visible_for_account(account_from_request(request)), username=username)
    events = _user_events(account, account_from_request(request))
    return TemplateResponse(
        request,
        "learnscripture/user_activity_stream.html",
        {
            "results": get_paged_results(events, request, 40),
            "account": account,
            "title": t("activity-user-page-title", dict(username=account.username)),
        },
    )


def activity_item(request, event_id):
    event = get_object_or_404(
        Event.objects.for_activity_stream(viewer=account_from_request(request)).prefetch_related("comments__author"),
        id=int(event_id),
    )
    return TemplateResponse(
        request,
        "learnscripture/activity_item.html",
        {
            "event": event,
            "title": t("activity-item-page-title", dict(username=event.account.public_username)),
        },
    )


def set_language(request):
    """
    Save the given language in the session, and in the user's preferences if logged in.
    """
    next_url = request.headers.get("Referer", "/")
    next_url = furl.furl(next_url).set(host=None, port=None, scheme=None).url

    if not url_has_allowed_host_and_scheme(next_url, settings.ALLOWED_HOSTS):
        next_url = "/"
    response = HttpResponseRedirect(next_url)

    if request.method == "POST":
        lang_code = request.POST.get(i18n_views.LANGUAGE_QUERY_PARAMETER)
        if lang_code and lang_code in settings.LANGUAGE_CODES:
            session.set_interface_language(request, lang_code)
            identity = getattr(request, "identity", None)
            if identity is not None:
                identity.interface_language = lang_code
                identity.save()
    return response


def task_queue_debug(request):
    message = request.GET.get("message", "[no message]")
    learnscripture.tasks.message.apply_async([message])
    return HttpResponse(f"Task queued with message: {message}")


def debug(request):
    if "crash" in request.GET:
        raise AssertionError("Crash!")
    return TemplateResponse(request, "learnscripture/debug.html", {})
