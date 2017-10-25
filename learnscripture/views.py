# -*- coding: utf-8 -*-
import csv
import urllib.parse
from datetime import date, timedelta

import django.contrib.auth
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordChangeView as AuthPasswordChangeView
from django.contrib.auth.views import PasswordResetView as AuthPasswordResetView
from django.contrib.sites.models import Site
from django.core import mail
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from paypal.standard.forms import PayPalPaymentsForm

import learnscripture.tasks
from accounts.forms import AccountDetailsForm, PreferencesForm
from accounts.models import Account, Identity
from awards.models import AnyLevel, Award, AwardType
from bibleverses.books import BIBLE_BOOK_COUNT, get_bible_book_name
from bibleverses.forms import VerseSetForm
from bibleverses.languages import LANGUAGE_CODE_INTERNAL, LANGUAGES
from bibleverses.models import (MAX_VERSES_FOR_SINGLE_CHOICE, InvalidVerseReference, TextType, TextVersion, VerseSet,
                                VerseSetType, get_passage_sections, is_continuous_set)
from bibleverses.parsing import internalize_localized_reference, localize_internal_reference, parse_break_list
from bibleverses.signals import public_verse_set_created
from events.models import Event
from groups.forms import EditGroupForm
from groups.models import Group
from groups.signals import public_group_created
from learnscripture import session
from learnscripture.forms import (AccountPasswordChangeForm, AccountPasswordResetForm, AccountSetPasswordForm,
                                  ContactForm, LogInForm, SignUpForm)
from payments.sign import sign_payment_info
from scores.models import (get_all_time_leaderboard, get_leaderboard_since, get_verses_started_counts,
                           get_verses_started_per_day, get_verses_tested_per_day)

from .decorators import (has_preferences, redirect_via_prefs, require_account, require_account_with_redirect,
                         require_identity, require_preferences)

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
#   as 'Guest user' (session.html template, and menu in base.html)
# - if there is an Identity, but no Account, they will still
#   appear as 'Guest user', but now have the possibility of stored
#   data and preferences.
#
# - We do need Identity and preferences to be set for some actions,
#   so we create it as needed, typically by the popup preferences form


USER_EVENTS_SHORT_CUTOFF = 5
GROUP_COMMENTS_SHORT_CUTOFF = 5


def missing(request, message, status_code=404):
    response = render(request, '404.html', {'message': message})
    response.status_code = status_code
    return response


def home(request):
    identity = getattr(request, 'identity', None)
    if identity is not None and identity.default_to_dashboard:
        return HttpResponseRedirect(reverse('dashboard'))
    return render(request, 'learnscripture/home.html')


def _login_redirect(request):
    return get_next(request, reverse('dashboard'))


def login(request):
    if account_from_request(request) is not None:
        return _login_redirect(request)

    if request.method == 'POST':
        form = LogInForm(request.POST, prefix="login")
        if 'signin' in request.POST:
            if form.is_valid():
                account = form.cleaned_data['account']
                account.last_login = timezone.now()
                account.save()
                # Make this login form work for admin:
                user = django.contrib.auth.authenticate(username=account.username,
                                                        password=form.cleaned_data['password'])
                django.contrib.auth.login(request, user)

                session.login(request, account.identity)
                return _login_redirect(request)
        elif 'forgotpassword' in request.POST:
            resetform = AccountPasswordResetForm(request.POST, prefix="login")
            if resetform.is_valid():
                # This will validate the form again, but it doesn't matter.
                return password_reset(request)
            else:
                # Need errors from password reset for be used on main form - hack
                form._errors = resetform.errors
    else:
        form = LogInForm(prefix="login")

    return render(request, "learnscripture/login.html",
                  {'title': 'Sign in',
                   'login_form': form})


class _PasswordResetView(AuthPasswordResetView):
    form_class = AccountPasswordResetForm
    email_template_name = 'learnscripture/password_reset_email.txt'

    def get_prefix(self):
        return "login"


password_reset = _PasswordResetView.as_view()


def signup(request):
    from accounts.signals import new_account

    c = {}
    if account_from_request(request) is not None:
        c['already_signed_up'] = True

    if request.method == 'POST':
        form = SignUpForm(request.POST, prefix="signup")

        if form.is_valid():
            identity = getattr(request, 'identity', None)
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
            messages.info(request, "Account created - welcome %s!" % account.username)
            new_account.send(sender=account)
            return _login_redirect(request)

    else:
        form = SignUpForm(prefix="signup")

    c['title'] = 'Create account'
    c['signup_form'] = form

    return render(request, "learnscripture/signup.html", c)


def feature_disallowed(request, title, reason):
    return render(request, 'learnscripture/feature_disallowed.html',
                  {'title': title,
                   'reason': reason,
                   })


def bible_versions_for_request(request):
    if hasattr(request, 'identity'):
        return request.identity.available_bible_versions()
    return TextVersion.objects.bibles().filter(public=True)


@require_preferences
def learn(request):
    c = {'bible_versions': bible_versions_for_request(request),
         'title': "Learn",
         }
    return render(request, 'learnscripture/learn.html', c)


def preferences(request):
    identity = getattr(request, 'identity', None)
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

            form.save()
            return get_next(request, reverse('dashboard'))
    else:
        form = PreferencesForm(instance=identity)
    c = {'form': form,
         'title': 'Preferences',
         'hide_preferences_popup': True}
    return render(request, 'learnscripture/preferences.html', c)


def account_from_request(request):
    if hasattr(request, 'identity'):
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
    if 'next' in request.GET:
        next = local_redirect(request.GET['next'])
        if next is not None:
            return HttpResponseRedirect(next)

    return HttpResponseRedirect(default_url)


def todays_stats(identity):
    stats = {}
    session_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    stats['total_verses_tested'] = set(uvs.localized_reference for uvs in
                                       identity.verse_statuses
                                       .filter(last_tested__gte=session_start,
                                               ignored=False)
                                       )
    stats['new_verses_started'] = set(uvs.localized_reference for uvs in
                                      identity.verse_statuses
                                      .filter(first_seen__gte=session_start,
                                              ignored=False)
                                      )
    return stats


def learn_set(request, uvs_list, learning_type):
    uvs_list = [u for u in uvs_list if u is not None]
    # Save where we should return to after learning:
    return_to = reverse('dashboard')  # by default, the dashboard
    referer = request.META.get('HTTP_REFERER')
    if referer is not None:
        url = urllib.parse.urlparse(referer)
        allowed_return_to = [reverse('user_verses')]  # places it is useful to return to
        if url.path in allowed_return_to:
            # avoiding redirection security problems by making it relative:
            url = ('', '', url.path, url.params, url.query, url.fragment)
            return_to = urllib.parse.urlunparse(url)

    session.start_learning_session(request, uvs_list, learning_type, return_to)
    return HttpResponseRedirect(reverse('learn'))


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
    groups = groups[0:limit + 1]  # + 1 so we can see if we got more
    if len(groups) > limit:
        return groups[0:3], True
    else:
        return groups, False


@never_cache
def dashboard(request):
    identity = getattr(request, 'identity', None)

    if identity is None:
        # Probably got here from a 'revision reminder' email,
        # so we are best redirecting them to log in.
        return HttpResponseRedirect(reverse('login'))

    if identity is None or not identity.verse_statuses.exists():
        # The only possible thing is to choose some verses
        return HttpResponseRedirect(reverse('choose'))

    if request.method == 'POST':

        get_catechism_id = lambda: int(request.POST['catechism_id'])

        if 'learnbiblequeue' in request.POST:
            if 'verse_set_id' in request.POST:
                vs_id = int(request.POST['verse_set_id'])
            else:
                vs_id = None
            return learn_set(request,
                             identity.bible_verse_statuses_for_learning(vs_id),
                             session.LearningType.LEARNING)
        if 'reviewbiblequeue' in request.POST:
            return learn_set(request, identity.bible_verse_statuses_for_reviewing(),
                             session.LearningType.REVISION)
        if 'learncatechismqueue' in request.POST:
            return learn_set(request, identity.catechism_qas_for_learning(get_catechism_id()),
                             session.LearningType.LEARNING)
        if 'reviewcatechismqueue' in request.POST:
            return learn_set(request, identity.catechism_qas_for_reviewing(get_catechism_id()),
                             session.LearningType.REVISION)
        if any(p in request.POST for p in
               ['learnpassage',
                'reviewpassage', 'reviewpassagenextsection', 'reviewpassagesection',
                'practisepassage', 'practisepassagesection']):

            # Some of these are sent via the verse_options.html template,
            # not from the dashboard.

            vs_id = int(request.POST['verse_set_id'])
            verse_set = VerseSet.objects.get(id=vs_id)

            if 'uvs_id' in request.POST:
                # Triggered from 'verse_options.html'
                uvs_id = int(request.POST['uvs_id'])
                main_uvs = identity.verse_statuses.get(id=uvs_id)
                version_id = main_uvs.version_id

                uvss = identity.verse_statuses_for_passage(vs_id, version_id)
                if ('reviewpassagesection' in request.POST or
                        'practisepassagesection' in request.POST):
                    # Review/practise the specified section
                    uvss = main_uvs.get_section_verse_status_list(uvss)
            else:
                version_id = request.POST['version_id']
                uvss = identity.verse_statuses_for_passage(vs_id, version_id)

            if 'learnpassage' in request.POST:
                uvss = identity.slim_passage_for_reviewing(uvss, verse_set)
                return learn_set(request, uvss, session.LearningType.LEARNING)
            if 'reviewpassage' in request.POST:
                uvss = identity.slim_passage_for_reviewing(uvss, verse_set)
                return learn_set(request, uvss, session.LearningType.REVISION)
            if 'reviewpassagenextsection' in request.POST:
                uvss = identity.get_next_section(uvss, verse_set)
                return learn_set(request, uvss, session.LearningType.REVISION)
            if 'reviewpassagesection' in request.POST:
                # Already filtered uvss above
                return learn_set(request, uvss, session.LearningType.REVISION)
            if 'practisepassage' in request.POST:
                return learn_set(request, uvss, session.LearningType.PRACTICE)
            if 'practisepassagesection' in request.POST:
                # Already filtered uvss above
                return learn_set(request, uvss, session.LearningType.PRACTICE)

        if 'reviewverse' in request.POST:
            uvs = identity.verse_statuses.get(id=int(request.POST['uvs_id']))
            return learn_set(request, [uvs],
                             session.LearningType.REVISION if uvs.needs_testing
                             else session.LearningType.PRACTICE)

        if 'reviewcatechism' in request.POST:
            # This option reviews catechism questions even if they are not
            # due for revision yet.
            uvss = identity.get_all_tested_catechism_qas(get_catechism_id())
            return learn_set(request, uvss,
                             session.LearningType.REVISION)

        if 'clearbiblequeue' in request.POST:
            if 'verse_set_id' in request.POST:
                vs_id = int(request.POST['verse_set_id'])
            else:
                vs_id = None
            identity.clear_bible_learning_queue(vs_id)
            return HttpResponseRedirect(reverse('dashboard'))
        if 'clearcatechismqueue' in request.POST:
            identity.clear_catechism_learning_queue(get_catechism_id())
            return HttpResponseRedirect(reverse('dashboard'))
        if 'cancelpassage' in request.POST:
            vs_id = int(request.POST['verse_set_id'])
            version_id = int(request.POST['version_id'])
            identity.cancel_passage(vs_id, version_id)
            return HttpResponseRedirect(reverse('dashboard'))

    groups, more_groups = get_user_groups(identity)

    c = {'learn_verses_queues': identity.bible_verse_statuses_for_learning_grouped(),
         'review_verses_queue': identity.bible_verse_statuses_for_reviewing(),
         'passages_for_learning': identity.passages_for_learning(),
         'passages_for_reviewing': identity.passages_for_reviewing(),
         'catechisms_for_learning': identity.catechisms_for_learning(),
         'catechisms_for_reviewing': identity.catechisms_for_reviewing(),
         'next_verse_due': identity.next_verse_due(),
         'title': 'Dashboard',
         'events': identity.get_dashboard_events(),
         'create_account_warning':
             identity.account is None and
         (timezone.now() - identity.date_created) > timedelta(days=3),
         'groups': groups,
         'more_groups': more_groups,
         'url_after_logout': '/',
         }
    c.update(todays_stats(identity))
    return render(request, 'learnscripture/dashboard.html', c)


def context_for_version_select(request):
    """
    Returns the context data needed to render a version select box
    """
    return {'bible_versions': bible_versions_for_request(request)}


def context_for_quick_find(request):
    """
    Returns the context data needed to render a quick find box
    """
    version = default_bible_version_for_request(request)
    language_codes = [l.code for l in LANGUAGES] + [LANGUAGE_CODE_INTERNAL]

    bible_books = [
        {lc: get_bible_book_name(lc, i)
         for lc in language_codes}
        for i in range(0, BIBLE_BOOK_COUNT)
    ]
    d = {'bible_books': bible_books,
         'default_bible_version': version,
         'language_codes': language_codes,
         'current_language_code': version.language_code,
         }
    d.update(context_for_version_select(request))
    return d


def default_bible_version_for_request(request):
    if has_preferences(request):
        return request.identity.default_bible_version
    else:
        return get_default_bible_version()


# No 'require_preferences' or 'require_identity' so that bots can browse this
# page and the linked pages unhindered, for SEO.

def choose(request):
    """
    Choose a verse or verse set
    """
    default_bible_version = default_bible_version_for_request(request)
    verse_sets = verse_sets_visible_for_request(request)

    if request.method == "POST":
        if not has_preferences(request):
            # Shouldn't get here if UI preferences javascript is working right.
            return redirect_via_prefs(request)

        identity = request.identity
        version = None
        try:
            version = TextVersion.objects.get(slug=request.POST['version_slug'])
        except (KeyError, TextVersion.DoesNotExist):
            version = default_bible_version

        # Handle choose set
        vs_id = request.POST.get('verseset_id', None)
        if vs_id is not None:
            try:
                vs = verse_sets.prefetch_related('verse_choices').get(id=vs_id)
            except VerseSet.DoesNotExist:
                # Shouldn't be possible by clicking on buttons.
                vs = None
            if vs is not None:
                return learn_set(request, identity.add_verse_set(vs, version=version),
                                 session.LearningType.LEARNING)

        # Handle choose individual verse
        ref = request.POST.get('localized_reference', None)
        if ref is not None:
            # First ensure it is valid
            try:
                version.get_verse_list(ref, max_length=MAX_VERSES_FOR_SINGLE_CHOICE)
            except InvalidVerseReference:
                pass  # Ignore the post.
            else:
                return learn_set(request, [identity.add_verse_choice(ref, version=version)],
                                 session.LearningType.LEARNING)

    c = {'title': 'Choose verses'}
    verse_sets = verse_sets.order_by('name').prefetch_related('verse_choices')

    if 'creator' in request.GET:
        try:
            current_account = account_from_request(request)
            creator = Account.objects.visible_for_account(current_account).get(username=request.GET['creator'])
        except Account.DoesNotExist:
            creator = None
        if creator is not None:
            verse_sets = verse_sets.filter(created_by=creator)
            c['creator'] = creator

    # Searching for verse sets is done via this view.
    # But looking up individual verses is done by AJAX,
    # so is missing here.

    if 'q' in request.GET:
        language_code = default_bible_version.language_code
        verse_sets = VerseSet.objects.search(language_code, verse_sets, request.GET['q'])

    if 'new' in request.GET:
        verse_sets = verse_sets.order_by('-date_added')
    else:  # popular, the default
        verse_sets = verse_sets.order_by('-popularity')
    c['verse_sets'] = verse_sets
    c['active_tab'] = 'verseset'
    c['default_bible_version'] = default_bible_version

    c.update(context_for_quick_find(request))

    return render(request, 'learnscripture/choose.html', c)


def view_catechism_list(request):
    if request.method == "POST":
        if not has_preferences(request):
            # Shouldn't get here if UI preferences javascript is working right.
            return redirect_via_prefs(request)
        try:
            catechism = TextVersion.objects.get(id=int(request.POST['catechism_id']))
        except (KeyError, ValueError, TextVersion.DoesNotExist):
            raise Http404
        return learn_set(request,
                         request.identity.add_catechism(catechism),
                         session.LearningType.LEARNING)

    c = {'catechisms': TextVersion.objects.catechisms(),
         'title': 'Catechisms',
         }
    return render(request, 'learnscripture/catechisms.html', c)


def view_catechism(request, slug):
    try:
        catechism = TextVersion.objects.get(slug=slug)
    except TextVersion.DoesNotExist:
        raise Http404

    c = {'title': catechism.full_name,
         'catechism': catechism,
         'questions': catechism.qapairs.order_by('order'),
         'learners': catechism.get_learners(),
         }

    return render(request, 'learnscripture/view_catechism.html', c)


def verse_options(request):
    """
    Returns a page fragment showing a list of learning options for
    the verse in request.GET['ref']
    """
    # This view is called from the 'progress' page where the list of verses
    # being learnt by a user is shown.
    if not hasattr(request, 'identity'):
        return HttpResponse("Error: not logged in")
    identity = request.identity
    ref = request.GET['ref']
    version_slug = request.GET['version_slug']
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
    return render(request,
                  "learnscripture/verse_options.html",
                  {'uvs_list': uvss}
                  )


def _reduce_uvs_set_for_verse(uvss):
    # Filters out multiple instances of non-
    l = []
    non_passage_seen = False
    for uvs in uvss:
        if not uvs.is_in_passage():
            if non_passage_seen:
                continue
            else:
                non_passage_seen = True
        l.append(uvs)
    return l


def get_default_bible_version():
    # Use NET as default version because:
    # - they let us use their version without royalties
    # - it is a modern readable version.
    return TextVersion.objects.get(slug='NET')


def verse_sets_visible_for_request(request):
    return VerseSet.objects.visible_for_account(account_from_request(request))


def get_verse_set_verse_list(version, verse_set):
    language_code = version.language_code

    verse_choices = list(verse_set.verse_choices.all())
    all_localized_references = [localize_internal_reference(language_code,
                                                            vc.internal_reference)
                                for vc in verse_choices]
    verses = version.get_verses_by_localized_reference_bulk(all_localized_references)

    verse_list = sorted(verses.values(), key=lambda v: v.bible_verse_number)
    verse_list = add_passage_breaks(language_code, verse_list, verse_set.breaks)

    retval = []
    added_verse_refs = set()
    for vc in verse_choices:
        localized_ref = localize_internal_reference(language_code, vc.internal_reference)
        if localized_ref in verses:
            v = verses[localized_ref]
            # Don't add a merged verse to the list multiple times
            if v.localized_reference not in added_verse_refs:
                retval.append(v)
                added_verse_refs.add(v.localized_reference)

    return retval


def view_verse_set(request, slug):
    verse_set = get_object_or_404(verse_sets_visible_for_request(request), slug=slug)
    c = {'include_referral_links': verse_set.public}

    version = None
    try:
        version = bible_versions_for_request(request).get(slug=request.GET['version'])
    except (KeyError, TextVersion.DoesNotExist):
        pass

    if version is None:
        if hasattr(request, 'identity') and request.identity.default_bible_version is not None:
            version = request.identity.default_bible_version
        else:
            version = get_default_bible_version()

    verse_list = get_verse_set_verse_list(version, verse_set)
    all_localized_references = [v.localized_reference for v in verse_list]

    if hasattr(request, 'identity') and request.identity.can_edit_verse_set(verse_set):
        if (verse_set.is_selection and is_continuous_set(verse_list)):
            c['show_convert_to_passage'] = True

            if request.method == 'POST':
                if 'convert_to_passage_set' in request.POST:
                    verse_set.set_type = VerseSetType.PASSAGE
                    verse_set.save()
                    verse_set.update_passage_id()
                    messages.info(request, "Verse set converted to 'passage' type")
                    c['show_convert_to_passage'] = False

    if request.method == 'POST':
        if "drop" in request.POST and hasattr(request, 'identity'):
            refs_to_drop = request.identity.which_in_learning_queue(all_localized_references, version)
            request.identity.cancel_learning(refs_to_drop, version.slug)
            messages.info(request, "Dropped %d verse(s) from learning queue." % len(refs_to_drop))

    if hasattr(request, 'identity'):
        c['can_edit'] = request.identity.can_edit_verse_set(verse_set)
        verses_started = request.identity.which_verses_started(all_localized_references, version)
        c['started_count'] = len(verses_started)

        if verse_set.is_selection:
            c['in_queue'] = len(request.identity.which_in_learning_queue(all_localized_references, version))
        else:
            c['in_queue'] = 0
    else:
        c['can_edit'] = False
        c['started_count'] = 0
        c['in_queue'] = 0

    c['verse_set'] = verse_set
    c['verse_list'] = verse_list
    c['version'] = version
    c['title'] = "Verse set: %s" % verse_set.name
    c.update(context_for_version_select(request))
    return render(request, 'learnscripture/single_verse_set.html', c)


def add_passage_breaks(language_code, verse_list, breaks):
    retval = []
    sections = get_passage_sections(language_code, verse_list, breaks)
    for i, section in enumerate(sections):
        for j, v in enumerate(section):
            # need break at beginning of every section except first
            v.break_here = j == 0 and i != 0
            retval.append(v)
    return retval


@require_preferences
def create_set_menu(request):
    return render(request, 'learnscripture/create_set_menu.html', {'title': "Create verse set"})


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

    version = request.identity.default_bible_version
    language_code = version.language_code

    if slug is not None:
        verse_set = get_object_or_404(request.identity.account.verse_sets_editable.filter(slug=slug))
        set_type = verse_set.set_type
        mode = 'edit'
    else:
        verse_set = None
        mode = 'create'

    title = ('Edit verse set' if verse_set is not None
             else 'Create selection set' if set_type == VerseSetType.SELECTION
             else 'Create passage set')

    c = {}

    def mk_verse_list(localized_reference_list, verse_dict):
        verses = []
        for ref in localized_reference_list:  # preserve order
            if ref in verse_dict:
                verses.append(verse_dict[ref])
        return verses

    c['set_type'] = VerseSetType.name_for_value[set_type]

    if request.method == 'POST':
        orig_verse_set_public = False if verse_set is None else verse_set.public

        form = VerseSetForm(request.POST, instance=verse_set)
        internal_reference_list_raw = [
            i for i in request.POST.get('internal_reference_list', '').split('|')
            if i
        ]
        localized_reference_list_raw = [localize_internal_reference(language_code, r)
                                        for r in internal_reference_list_raw]
        verse_dict = version.get_verses_by_localized_reference_bulk(localized_reference_list_raw)

        # Dedupe localized_reference_list, and ensure correct references, while preserving order:
        localized_reference_list = []
        for ref in localized_reference_list_raw:
            if ref in verse_dict and ref not in localized_reference_list:
                localized_reference_list.append(ref)

        # Need to build an internal list that doesn't have merged verses.
        internal_reference_list = []
        for ref in localized_reference_list:
            verse = verse_dict[ref]
            sub_verses = verse.get_unmerged_parts()
            for v in sub_verses:
                internal_reference_list.append(internalize_localized_reference(version.language_code, v.localized_reference))

        breaks = normalize_break_list(request.POST.get('break_list', ''))

        form_is_valid = form.is_valid()
        if len(verse_dict) == 0:
            form.errors.setdefault('__all__', form.error_class()).append("No verses in set")
            form_is_valid = False

        if form_is_valid:
            # If all have a 'break' applied, (excluding first, which never has
            # one) then the user clearly doesn't understand the concept of
            # section breaks:
            tmp_verse_list = add_passage_breaks(
                language_code,
                mk_verse_list(localized_reference_list,
                              verse_dict),
                breaks)
            if all(v.break_here for v in tmp_verse_list[1:]):
                breaks = ""

            verse_set = form.save(commit=False)
            verse_set.set_type = set_type
            if verse_set.created_by_id is None:
                verse_set.created_by = request.identity.account
            verse_set.breaks = breaks

            if orig_verse_set_public:
                # Can't undo:
                verse_set.public = True
            verse_set.save()
            verse_set.set_verse_choices(internal_reference_list)

            # if user just made it public or it is a new public verse set
            if (verse_set.public and (not orig_verse_set_public or
                                      mode == 'create'
                                      )):
                public_verse_set_created.send(sender=verse_set)

            messages.info(request, "Verse set '%s' saved!" % verse_set.name)
            return HttpResponseRedirect(reverse('view_verse_set', kwargs=dict(slug=verse_set.slug)))

    else:
        form = VerseSetForm(instance=verse_set)

        if verse_set is not None:
            localized_reference_list = [vc.get_localized_reference(language_code)
                                        for vc in verse_set.verse_choices.all()]
            verse_dict = version.get_verses_by_localized_reference_bulk(localized_reference_list)
            breaks = verse_set.breaks
        else:
            localized_reference_list, verse_dict, breaks = [], {}, ''

    verse_list = mk_verse_list(localized_reference_list, verse_dict)
    if set_type == VerseSetType.PASSAGE:
        verse_list = add_passage_breaks(language_code, verse_list, breaks)

    c['verses'] = verse_list
    c['new_verse_set'] = verse_set is None
    c['verse_set_form'] = form
    c['title'] = title

    c.update(context_for_quick_find(request))

    return render(request, 'learnscripture/create_set.html', c)


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


def user_stats(request, username):
    viewer = account_from_request(request)
    account = get_object_or_404(Account.objects.visible_for_account(viewer)
                                .select_related('total_score', 'identity'),
                                username=username)
    c = {'account': account,
         'title': account.username,
         'awards': account.visible_awards(),
         'include_referral_links': True,
         'events': _user_events(account, viewer)[:USER_EVENTS_SHORT_CUTOFF]
         }

    if viewer is not None:
        c['viewer_is_following'] = viewer.is_following(account)

    one_week_ago = timezone.now() - timedelta(7)

    c['verses_started_all_time'] = account.identity.verses_started_count()
    c['verses_started_this_week'] = account.identity.verses_started_count(started_since=one_week_ago)
    c['verses_finished_all_time'] = account.identity.verses_finished_count()
    c['verses_finished_this_week'] = account.identity.verses_finished_count(finished_since=one_week_ago)
    c['verse_sets_created_all_time'] = account.verse_sets_created.count()
    c['verse_sets_created_this_week'] = account.verse_sets_created.filter(date_added__gte=one_week_ago).count()
    current_account = account_from_request(request)
    if current_account is not None and current_account == account:
        account_groups = account.get_groups()
    else:
        account_groups = account.get_public_groups()
    viewer_visible_groups = Group.objects.visible_for_account(viewer)
    c['groups'] = viewer_visible_groups.filter(id__in=[g.id for g in account_groups])
    return render(request, 'learnscripture/user_stats.html', c)


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


def user_stats_verses_timeline_stats_csv(request, username):
    account = get_object_or_404(Account.objects.active().filter(username=username))
    identity = account.identity
    started = get_verses_started_per_day(identity.id)
    tested = get_verses_tested_per_day(account.id)

    rows = combine_timeline_stats(started, tested)

    resp = HttpResponse(content_type="text/plain")
    writer = csv.writer(resp)
    writer.writerow(["Date", "Verses started", "Verses tested"])
    for d, c1, c2 in rows:
        writer.writerow([d.strftime("%Y-%m-%d"), c1, c2])
    return resp


@require_identity
def user_verses(request):
    identity = request.identity
    c = {'title': 'Progress'}

    # verse_statuses_started contains dupes, we do deduplication in the
    # template.
    verses = identity.verse_statuses_started().select_related('version')

    if 'catechisms' in request.GET:
        text_type = TextType.CATECHISM
    else:
        text_type = TextType.BIBLE

    verses = verses.filter(version__text_type=text_type)

    if text_type == TextType.CATECHISM:
        verses = verses.order_by('version__slug', 'text_order')
    else:
        if 'bibleorder' in request.GET:
            c['bibleorder'] = True
            verses = verses.order_by('text_order', 'strength')
        else:
            verses = verses.order_by('strength', 'localized_reference')
    c['verses'] = verses
    c['bible'] = text_type == TextType.BIBLE
    c['catechism'] = text_type == TextType.CATECHISM

    return render(request, 'learnscripture/user_verses.html', c)


@require_identity
def user_verse_sets(request):
    identity = request.identity
    c = {'title': 'Verse sets',
         'chosen_verse_sets': identity.verse_sets_chosen(),
         }
    if identity.account is not None:
        c['verse_sets_created'] = identity.account.verse_sets_created.all().order_by('name')

    return render(request, 'learnscripture/user_verse_sets.html', c)


# Password reset for Accounts:
#
# We can re-use a large amount of django.contrib.auth functionality
# due to same interface between Account and User. Some things need
# customising replacing.
#
# Also, we do the main password_reset via AJAX,
# from the the same form as the login form.
def password_reset_done(request):
    return render(request, 'learnscripture/password_reset_done.html',
                  {'title': 'Password reset started'})


def password_reset_complete(request):
    return render(request, 'learnscripture/password_reset_complete.html',
                  {'title': 'Password reset complete'})


# Large copy and paste from django.contrib.auth.views, followed by customisations.
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
    post_reset_redirect = reverse('password_reset_complete')
    try:
        uid_int = urlsafe_base64_decode(uidb64)
        user = Account.objects.get(id=uid_int)
    except (ValueError, Account.DoesNotExist):
        user = None

    if user is not None and token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            form = set_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(post_reset_redirect)
        else:
            form = set_password_form(None)
    else:
        validlink = False
        form = None
    context = {
        'form': form,
        'validlink': validlink,
        'title': 'Password reset',
    }
    return render(request, 'learnscripture/password_reset_confirm.html', context)


class _PasswordChangeView(AuthPasswordChangeView):
    template_name = "learnscripture/password_change_form.html"
    success_url = reverse_lazy('learnscripture_password_change_done')
    form_class = AccountPasswordChangeForm


password_change = require_account(_PasswordChangeView.as_view())


def password_change_done(request):
    return render(request, "learnscripture/password_change_done.html",
                  {})


def csrf_failure(request, reason=""):
    """
    Default view used when request fails CSRF protection
    """
    from django.middleware.csrf import REASON_NO_CSRF_COOKIE
    resp = render(request, "csrf_failure.html",
                  {'no_csrf_cookie': reason == REASON_NO_CSRF_COOKIE})
    resp.status_code = 403
    return resp


@require_account_with_redirect
def account_details(request):
    if request.method == 'POST':
        form = AccountDetailsForm(request.POST, instance=request.identity.account)
        if form.is_valid():
            form.save()
            messages.info(request, "Account details updated, thank you")
            return HttpResponseRedirect(reverse('account_details'))
    else:
        form = AccountDetailsForm(instance=request.identity.account)

    return TemplateResponse(request, 'learnscripture/account_details.html',
                            {'form': form,
                             'title': "Account details",
                             'url_after_logout': '/',
                             })


def date_to_js_ts(d):
    """
    Converts a date object to the timestamp required by the flot library
    """
    return int(d.strftime('%s')) * 1000


def stats(request):
    from app_metrics.models import MetricDay
    now = timezone.now()
    period = int(request.GET.get('period', 180))
    start = now - timedelta(days=period)

    def build_data(metric_slugs):
        metrics = (MetricDay.objects
                   .filter(metric__slug__in=metric_slugs)
                   .filter(created__gte=start)
                   .select_related('metric'))

        # Missing metrics => zero. However, if we omit a value for a day, then the
        # plotting library interpolates, when we want it to say zero.  So we have to
        # build a dictionary of all values and loop through by day.

        min_date = None
        max_date = now.date()

        grouped = {}
        for m in metrics:
            if min_date is None or m.created < min_date:
                min_date = m.created
            grouped[(m.metric.slug, m.created)] = m.num

        output_rows = dict((s, []) for s in metric_slugs)
        if min_date is None:
            min_date = start.date()
        cur_date = min_date
        while cur_date <= max_date:
            for s in metric_slugs:
                val = grouped.get((s, cur_date), 0)
                ts = date_to_js_ts(cur_date)
                output_rows[s].append((ts, val))
            cur_date += timedelta(1)
        return output_rows

    verses_data = build_data(['verse_started', 'verse_tested'])
    account_data = build_data(['new_account'] +
                              (['accounts_active',
                                'identities_active',
                                ] if 'full_accounts' in request.GET else []))

    return render(request, 'learnscripture/stats.html',
                  {'title': 'Stats',
                   'verses_data': verses_data,
                   'account_data': account_data,
                   })


def natural_list(l):
    if len(l) == 0:
        return ''
    if len(l) == 1:
        return l[0]
    return "%s and %s" % (", ".join(l[0:-1]), l[-1])


def donation_paypal_dict(account, url_start):
    return {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "item_name": "Donation to LearnScripture.net",
        "invoice": "account-%s-%s" % (account.id,
                                      timezone.now()),  # We don't need this, but must be unique
        "notify_url": "%s%s" % (url_start, reverse('paypal-ipn')),
        "return_url": "%s%s" % (url_start, reverse('pay_done')),
        "cancel_return": "%s%s" % (url_start, reverse('pay_cancelled')),
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
    if getattr(settings, 'STAGING', False):
        # Sometimes for staging site, we have a DB that has been dumped from production,
        # but needs Site object updated. Stop here, or payment testing won't work.
        assert domain.startswith('staging.')
    protocol = 'https' if request.is_secure() else 'http'
    return "%s://%s" % (protocol, domain)


def donate(request):
    c = {'title': 'Donate'}

    account = account_from_request(request)
    if account is not None:
        url_start = paypal_url_start_for_request(request)
        paypal_dict = donation_paypal_dict(account, url_start)
        form = PayPalPaymentsForm(initial=paypal_dict)
        c['LIVEBOX'] = settings.LIVEBOX
        c['paypal_form'] = form

    return render(request, 'learnscripture/donate.html', c)


@csrf_exempt
def pay_done(request):
    identity = getattr(request, 'identity', None)
    if identity is not None:
        if identity.account is not None:
            return HttpResponseRedirect(reverse('dashboard'))

    return render(request, 'learnscripture/pay_done.html', {'title': "Donation complete"})


@csrf_exempt
def pay_cancelled(request):
    return render(request, 'learnscripture/pay_cancelled.html', {'title': "Donation cancelled"})


def referral_program(request):
    account = account_from_request(request)
    if account is not None:
        referral_link = account.make_referral_link('https://%s/' % Site.objects.get_current().domain)
    else:
        referral_link = None

    return render(request, 'learnscripture/referral_program.html',
                  {'title': 'Referral program',
                   'referral_link': referral_link,
                   'include_referral_links': True,
                   })


def awards(request):
    award_classes = [AwardType.classes[t] for t in AwardType.values]
    awards = [cls(level=AnyLevel) for cls in award_classes if not cls.removed]
    discovered_awards = []
    hidden_awards = []
    for award in awards:
        if award.highest_level_achieved is None:
            hidden_awards.append(award)
        else:
            discovered_awards.append(award)

    return render(request, 'learnscripture/awards.html',
                  {'title': 'Badges',
                   'discovered_awards': discovered_awards,
                   'hidden_awards': hidden_awards,
                   })


def award(request, award_slug):
    award_name = award_slug.replace('-', '_').upper()
    award_type = AwardType.get_value_for_name(award_name)
    if award_type is None:
        raise Http404
    if not Award.objects.filter(award_type=award_type).exists():
        raise Http404
    award_class = AwardType.classes[award_type]
    if award_class.removed:
        return missing(request, "The ‘{0}’ award is an old award that is no longer used".format(award_class.title), status_code=410)
    award = award_class(level=AnyLevel)

    levels = []

    hellbanned_mode = get_hellbanned_mode(request)
    for level in range(award.max_level, 0, -1):
        awards = Award.objects.filter(award_type=award_type,
                                      account__is_active=True,
                                      level=level)
        if not hellbanned_mode:
            awards = awards.exclude(account__is_hellbanned=True)

        receivers_count = awards.count()
        if receivers_count > 0:
            sample_usernames = list(awards.order_by('-created')
                                    .values_list('account__username', flat=True)
                                    [0:5]
                                    )
            levels.append((level, receivers_count, sample_usernames))

    account_top_award = None
    account = account_from_request(request)
    if account is not None:
        try:
            account_top_award = account.awards.filter(award_type=award_type).order_by('-level')[0]
        except IndexError:
            pass

    return render(request, 'learnscripture/award.html',
                  {'title': 'Badge - %s' % award.short_description(),
                   'award': award,
                   'levels': levels,
                   'account_top_award': account_top_award,
                   })


def groups_visible_for_request(request):
    return Group.objects.visible_for_account(account_from_request(request))


def groups_editable_for_request(request):
    return Group.objects.editable_for_account(account_from_request(request))


def groups(request):
    account = account_from_request(request)
    groups = Group.objects.visible_for_account(account).order_by('name')
    if 'q' in request.GET:
        q = request.GET['q']
        groups = (groups.filter(name__icontains=q) |
                  groups.filter(description__icontains=q)
                  )
    return render(request, 'learnscripture/groups.html', {'title': 'Groups',
                                                          'groups': groups,
                                                          })


def group_by_slug(request, slug):
    groups = groups_visible_for_request(request)
    return get_object_or_404(groups,
                             slug=slug)


def group(request, slug):
    group = group_by_slug(request, slug)
    account = account_from_request(request)

    if request.method == "POST":
        if account is None:
            return HttpResponseRedirect(reverse('signup') +
                                        "?next=" + urllib.parse.quote(request.get_full_path()))

        if 'leave' in request.POST:
            group.remove_user(account)
            messages.info(request, "Removed you from group %s" % group.name)
            return HttpResponseRedirect(request.get_full_path())
        if 'join' in request.POST:
            if group.can_join(account):
                group.add_user(account)
                messages.info(request, "Added you to group %s" % group.name)
            return HttpResponseRedirect(request.get_full_path())

    if account is not None:
        in_group = group.members.filter(id=account.id).exists()
    else:
        in_group = False

    return render(request, 'learnscripture/group.html',
                  {'title': 'Group: %s' % group.name,
                   'group': group,
                   'in_group': in_group,
                   'can_join': group.can_join(account),
                   'can_edit': group.can_edit(account),
                   'include_referral_links': True,
                   'comments': reversed(group.comments_visible_for_account(account).order_by('-created')[:GROUP_COMMENTS_SHORT_CUTOFF])
                   })


def group_wall(request, slug):
    account = account_from_request(request)
    group = group_by_slug(request, slug)

    # TODO: respond to 'comment' query param and move to the right page of
    # comments.
    return render(request, 'learnscripture/group_wall.html',
                  {'title': 'Group wall: %s' % group.name,
                   'group': group,
                   'comments': group.comments_visible_for_account(account).order_by('created'),
                   })


def group_leaderboard(request, slug):
    page_num = None  # 1-indexed page page
    try:
        page_num = int(request.GET['p'])
    except (KeyError, ValueError):
        page_num = 1

    thisweek = 'thisweek' in request.GET

    page_num = max(1, page_num)

    PAGE_SIZE = 30

    if thisweek:
        cutoff = timezone.now() - timedelta(7)
    else:
        cutoff = None

    group = group_by_slug(request, slug)

    hellbanned_mode = get_hellbanned_mode(request)
    if thisweek:
        accounts = get_leaderboard_since(cutoff, hellbanned_mode,
                                         page_num - 1, PAGE_SIZE, group=group)
    else:
        accounts = get_all_time_leaderboard(hellbanned_mode, page_num - 1,
                                            PAGE_SIZE, group=group)

    # Now decorate these accounts with additional info from additional queries
    account_ids = [a['account_id'] for a in accounts]
    # identities and account info
    identities = Identity.objects.filter(account__id__in=account_ids).select_related('account')
    identity_ids = [i.id for i in identities]
    identity_dict = dict((i.account_id, i) for i in identities)

    # Counts of verses learnt
    verse_counts = get_verses_started_counts(identity_ids, cutoff)

    for account_dict in accounts:
        identity = identity_dict[account_dict['account_id']]
        account_dict['num_verses'] = verse_counts[identity.id]
        account_dict['username'] = identity.account.username

    c = {}
    c['include_referral_links'] = True
    c['accounts'] = accounts
    c['thisweek'] = thisweek
    c['page_num'] = page_num
    c['previous_page_num'] = page_num - 1
    c['next_page_num'] = page_num + 1
    c['PAGE_SIZE'] = PAGE_SIZE
    c['group'] = group
    c['title'] = "Leaderboard: {0}".format(group.name)
    return render(request, 'learnscripture/leaderboard.html', c)


def create_group(request):
    return create_or_edit_group(request)


def edit_group(request, slug):
    return create_or_edit_group(request, slug=slug)


@require_account_with_redirect
def create_or_edit_group(request, slug=None):
    account = account_from_request(request)
    if slug is not None:
        groups = groups_editable_for_request(request).filter(slug=slug)
        group = get_object_or_404(groups)
        title = 'Edit group: %s' % group.name
        initial = {'invited_users': group.invited_users()}
    else:
        group = None
        title = "Create group"
        initial = {}

    was_public = group.public if group is not None else False

    if request.method == 'POST':
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
            group.set_invitation_list(form.cleaned_data['invited_users'])
            messages.info(request, "Group details saved.")
            return HttpResponseRedirect(reverse('group', args=(group.slug,)))
    else:
        form = EditGroupForm(instance=group, initial=initial)

    return render(request, 'learnscripture/edit_group.html',
                  {'title': title,
                   'group': group,
                   'form': form,
                   })


def group_select_list(request):
    account = account_from_request(request)
    groups = list(Group.objects.visible_for_account(account))
    if account is not None:
        own_groups = set(account.get_groups())
        for g in groups:
            g.is_member = g in own_groups
        groups.sort(key=lambda g: not g.is_member)
    return render(request, 'learnscripture/group_select_list.html',
                  {'groups': groups})


def terms_of_service(request):
    return render(request, 'learnscripture/terms_of_service.html',
                  {'title': 'Terms of service'})


def contact(request):
    account = account_from_request(request)
    if account is not None:
        initial = {'name': account.first_name + ' ' + account.last_name,
                   'email': account.email}
    else:
        initial = {}
    if request.method == 'POST':
        form = ContactForm(request.POST, initial=initial)
        if form.is_valid():
            send_contact_email(form, account)
            return HttpResponseRedirect('/contact/thanks/')
    else:
        form = ContactForm(initial=initial)
    return render(request, 'learnscripture/contact.html',
                  {'title': 'Contact us',
                   'form': form,
                   })


def send_contact_email(contact_form, account):
    email = contact_form.cleaned_data['email']
    mail.EmailMessage(subject="LearnScripture feedback",
                      body="""
From: %(name)s
Email: %(email)s
Account: %(account)s
Message:

%(message)s
""" % {
    'name': contact_form.cleaned_data['name'],  # noqa
    'email': email,
    'account': account.username if account is not None else '',
    'message': contact_form.cleaned_data['message'],
},
                      from_email=settings.SERVER_EMAIL,
                      to=[settings.CONTACT_EMAIL],
                      headers={'Reply-To': email} if email else {},
    ).send()


def activity_stream(request):
    viewer = account_from_request(request)
    return render(request,
                  'learnscripture/activity_stream.html',
                  {'events':
                   Event.objects
                   .for_activity_stream(viewer=viewer)
                   .prefetch_related('comments', 'comments__author'),
                   'title': "Recent activity",
                   'following_ids': [] if viewer is None
                   else [a.id for a in viewer.following.all()]
                   })


def _user_events(for_account, viewer):
    return (Event.objects
            .for_activity_stream(viewer=viewer,
                                 event_by=for_account,
                                 )
            .prefetch_related('comments', 'comments__author')
            )


def user_activity_stream(request, username):
    account = get_object_or_404(Account.objects.visible_for_account(account_from_request(request)),
                                username=username)

    return render(request,
                  'learnscripture/user_activity_stream.html',
                  {'account': account,
                   'events': _user_events(account, account_from_request(request)),
                   'title': "Recent activity from %s" % account.username,
                   })


def activity_item(request, event_id):
    event = get_object_or_404(Event.objects
                              .for_activity_stream(viewer=account_from_request(request))
                              .prefetch_related('comments__author'),
                              id=int(event_id))

    return render(request,
                  'learnscripture/activity_item.html',
                  {'event': event,
                   'title': "Activity from %s" % event.account.username,
                   })


def celery_debug(request):
    message = request.GET.get('message', '[no message]')
    learnscripture.tasks.message.apply_async([message])
    return HttpResponse("Task queued with message: {0}".format(message))
