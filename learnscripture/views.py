
from datetime import timedelta
from decimal import Decimal
import re

from django.db import models
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core import mail
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.http import urlparse, base36_to_int
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters

from paypal.standard.forms import PayPalPaymentsForm

from accounts import memorymodel
from accounts.models import Account, Identity
from accounts.forms import PreferencesForm, AccountDetailsForm
from awards.models import AwardType, AnyLevel, Award
from learnscripture.forms import AccountSetPasswordForm, ContactForm
from bibleverses.models import VerseSet, TextVersion, BIBLE_BOOKS, InvalidVerseReference, MAX_VERSES_FOR_SINGLE_CHOICE, VerseChoice, VerseSetType, get_passage_sections, get_verses_started_counts
from bibleverses.signals import public_verse_set_created
from learnscripture import session, auth
from bibleverses.forms import VerseSetForm
from groups.forms import EditGroupForm
from groups.models import Group
from groups.signals import public_group_created
from payments.sign import sign_payment_info
from scores.models import get_all_time_leaderboard, get_leaderboard_since, ScoreReason

from .decorators import require_identity, require_preferences, has_preferences, redirect_via_prefs, require_account, require_account_with_redirect

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


def home(request):
    identity = getattr(request, 'identity', None)
    if identity is not None and identity.default_to_dashboard:
        return HttpResponseRedirect(reverse('dashboard'))
    return render(request, 'learnscripture/home.html')


# See comment in accounts.js for why this required (and doesn't do any logging
# in).
def login(request):
    # Redirect to dashboard because just about everything you might want to do
    # will change after sign in, and we want to encourage people to do their
    # revision first.
    # Allow a url to be passed in the query string too.
    return get_next(request, reverse('dashboard'))


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
         'title': u"Learn",
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
    c = {'form':form,
         'title': u'Preferences',
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
    netloc = urlparse.urlparse(url)[1]
    return None if netloc else url


def get_next(request, default_url):
    if 'next' in request.GET:
        next = local_redirect(request.GET['next'])
        if next is not None:
            return HttpResponseRedirect(next)

    return HttpResponseRedirect(default_url)


# Arbitrarily set 4 hours as max length of 'session' of learning
SESSION_LENGTH_HOURS = 4

def session_stats(identity):
    stats = {}
    now = timezone.now()
    session_start = now - timedelta(hours=SESSION_LENGTH_HOURS)
    all_verses_tested = identity.verse_statuses.filter(last_tested__gte=session_start,
                                                       ignored=False)
    # Need to dedupe for case of multiple UserVerseStatus for same verse
    # (due to different versions and different VerseChoice objects)
    all_verses_tested = list(all_verses_tested)
    stats['new_verses_tested'] = set(uvs.reference for uvs in all_verses_tested
                                     if uvs.first_seen is not None
                                     and uvs.first_seen > session_start)
    stats['total_verses_tested'] = set(uvs.reference for uvs in all_verses_tested)
    return stats


def learn_set(request, uvs_list, learning_type):
    return_to = reverse('dashboard')
    referer = request.META.get('HTTP_REFERER')
    if referer is not None:
        url = urlparse.urlparse(referer)
        allowed_return_to = [reverse('user_verses')]
        if url.path in allowed_return_to:
            # avoiding redirection security problems by making it relative:
            url = ('', '', url.path, url.params, url.query, url.fragment)
            return_to = urlparse.urlunparse(url)

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
    groups = groups[0:limit + 1] # + 1 so we can see if we got more
    if len(groups) > limit:
        return groups[0:3], True
    else:
        return groups, False

# Dashboard:
def dashboard(request):

    identity = getattr(request, 'identity', None)

    if identity is None or not identity.verse_statuses.exists():
        # The only possible thing is to choose some verses
        return HttpResponseRedirect(reverse('choose'))

    if request.method == 'POST':
        if 'learnqueue' in request.POST:
            return learn_set(request, identity.verse_statuses_for_learning(),
                             session.LearningType.LEARNING)
        if 'revisequeue' in request.POST:
            return learn_set(request, identity.verse_statuses_for_revising(),
                             session.LearningType.REVISION)
        if any(p in request.POST for p in
               ['learnpassage',
                'revisepassage', 'revisepassagenextsection', 'revisepassagesection',
                'practisepassage', 'practisepassagesection']):

            # Some of these are sent via the verse_options.html template,
            # not from the dashboard.

            vs_id = int(request.POST['verse_set_id'])
            verse_set = VerseSet.objects.get(id=vs_id)
            uvss = identity.verse_statuses_for_passage(vs_id)

            if 'uvs_id' in request.POST:
                # Triggered from 'verse_options.html'
                uvs_id = int(request.POST['uvs_id'])
                main_uvs = [uvs for uvs in uvss if uvs.id == uvs_id][0]
                if ('revisepassagesection' in request.POST or
                    'practisepassagesection' in request.POST):
                    # Revise/practise the specified section
                    refs = set(vc.reference for vc in main_uvs.get_section_verse_choices())
                    uvss = [uvs for uvs in uvss if uvs.reference in refs]

            if 'learnpassage' in request.POST:
                uvss = identity.slim_passage_for_revising(uvss, verse_set)
                return learn_set(request, uvss, session.LearningType.LEARNING)
            if 'revisepassage' in request.POST:
                uvss = identity.slim_passage_for_revising(uvss, verse_set)
                return learn_set(request, uvss, session.LearningType.REVISION)
            if 'revisepassagenextsection' in request.POST:
                uvss = identity.get_next_section(uvss, verse_set)
                return learn_set(request, uvss, session.LearningType.REVISION)
            if 'revisepassagesection' in request.POST:
                # Already filtered uvss above
                return learn_set(request, uvss, session.LearningType.REVISION)
            if 'practisepassage' in request.POST:
                return learn_set(request, uvss, session.LearningType.PRACTICE)
            if 'practisepassagesection' in request.POST:
                # Already filtered uvss above
                return learn_set(request, uvss, session.LearningType.PRACTICE)

        if 'reviseverse' in request.POST:
            uvs = identity.verse_statuses.get(id=int(request.POST['uvs_id']))
            return learn_set(request, [uvs],
                             session.LearningType.REVISION if uvs.needs_testing
                             else session.LearningType.PRACTICE)

        if 'clearqueue' in request.POST:
            identity.clear_learning_queue()
            return HttpResponseRedirect(reverse('dashboard'))
        if 'cancelpassage' in request.POST:
            vs_id = int(request.POST['verse_set_id'])
            identity.cancel_passage(vs_id)
            return HttpResponseRedirect(reverse('dashboard'))

    groups, more_groups = get_user_groups(identity)

    c = {'new_verses_queue': identity.verse_statuses_for_learning(),
         'revise_verses_queue': identity.verse_statuses_for_revising(),
         'passages_for_learning': identity.passages_for_learning(),
         'passages_for_revising': identity.passages_for_revising(),
         'next_verse_due': identity.next_verse_due(),
         'title': 'Dashboard',
         'events': identity.get_dashboard_events(),
         'create_account_warning':
             identity.account is None and
         (timezone.now() - identity.date_created) > timedelta(days=3),
         'groups': groups,
         'more_groups': more_groups,
         }
    c.update(session_stats(identity))
    return render(request, 'learnscripture/dashboard.html', c)


def context_for_version_select(request):
    return {'bible_versions': bible_versions_for_request(request)}


def context_for_quick_find(request):
    """
    Returns the context data needed to render a version select box
    """
    d = {'BIBLE_BOOKS': BIBLE_BOOKS,
         'default_bible_version': default_bible_version_for_request(request)
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
                vs = identity.verse_sets_visible().prefetch_related('verse_choices').get(id=vs_id)
            except VerseSet.DoesNotExist:
                # Shouldn't be possible by clicking on buttons.
                pass
            if vs is not None:
                return learn_set(request, identity.add_verse_set(vs, version=version),
                                 session.LearningType.LEARNING)

        # Handle choose individual verse
        ref = request.POST.get('reference', None)
        if ref is not None:
            # First ensure it is valid
            try:
                version.get_verse_list(ref, max_length=MAX_VERSES_FOR_SINGLE_CHOICE)
            except InvalidVerseReference:
                pass # Ignore the post.
            else:
                return learn_set(request, [identity.add_verse_choice(ref, version=version)],
                                 session.LearningType.LEARNING)

    c = {'title': u'Choose verses'}
    verse_sets = verse_sets_visible_for_request(request).order_by('name').prefetch_related('verse_choices')

    # Searching for verse sets is done via this view.
    # But looking up individual verses is done by AJAX,
    # so is missing here.

    if 'q' in request.GET:
        verse_sets = verse_sets.filter(name__icontains=request.GET['q'])

    if 'new' in request.GET:
        verse_sets = verse_sets.order_by('-date_added')
    else: # popular, the default
        verse_sets = verse_sets.order_by('-popularity')
    c['verse_sets'] = verse_sets
    c['active_tab'] = 'verseset'

    c.update(context_for_quick_find(request))

    return render(request, 'learnscripture/choose.html', c)


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
    # - could *revise*
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
    if hasattr(request, 'identity'):
        return request.identity.verse_sets_visible()
    else:
        return VerseSet.objects.public()


def is_continuous_set(verse_list):
    bvns = [v.bible_verse_number for v in verse_list]
    return bvns == list(range(verse_list[0].bible_verse_number,
                              verse_list[-1].bible_verse_number + 1))


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

    # Decorate the verse choices with the text.
    verse_choices = list(verse_set.verse_choices.all())
    all_references = [vc.reference for vc in verse_choices]
    verses = version.get_verses_by_reference_bulk(all_references)

    # Decorate verses with break information.
    verse_list = sorted(verses.values(), key=lambda v: v.bible_verse_number)
    verse_list = add_passage_breaks(verse_list, verse_set.breaks)

    for vc in verse_choices:
        vc.verse = verses[vc.reference]

    if (verse_set.set_type == VerseSetType.SELECTION and
        len(verse_list) > 1 and is_continuous_set(verse_list)):
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
            refs_to_drop = request.identity.which_in_learning_queue(all_references)
            request.identity.cancel_learning(refs_to_drop)
            messages.info(request, "Dropped %d verse(s) from learning queue." % len(refs_to_drop))

    if hasattr(request, 'identity'):
        c['can_edit'] = verse_set.created_by_id == request.identity.account_id
        verses_started = request.identity.which_verses_started(all_references)
        c['started_count'] = len(verses_started)

        if verse_set.set_type == VerseSetType.SELECTION:
            c['in_queue'] = len(request.identity.which_in_learning_queue(all_references))
        else:
            c['in_queue'] = 0
    else:
        c['can_edit'] = False
        c['started_count'] = 0
        c['in_queue'] = 0

    c['verse_set'] = verse_set
    c['verse_choices'] = verse_choices
    c['version'] = version
    c['title'] = u"Verse set: %s" % verse_set.name
    c.update(context_for_version_select(request))
    return render(request, 'learnscripture/single_verse_set.html', c)



def add_passage_breaks(verse_list, breaks):
    retval = []
    sections = get_passage_sections(verse_list, breaks)
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


def create_or_edit_set(request, set_type=None, slug=None):

    # This view handles a lot (too much)!  It could be simplified by removing
    # the form prefixes that distinguish between passage and selection sets,
    # which are no longer needed. But various bits of CSS and javascript would
    # need updating.

    version = request.identity.default_bible_version

    if slug is not None:
        verse_set = get_object_or_404(request.identity.account.verse_sets_created.filter(slug=slug))
        set_type = verse_set.set_type
        mode = 'edit'
    else:
        verse_set = None
        mode = 'create'

    title = ('Edit verse set' if verse_set is not None
             else 'Create selection set' if set_type == VerseSetType.SELECTION
             else 'Create passage set')

    allowed, reason = auth.check_allowed(request, auth.Feature.CREATE_VERSE_SET)
    if not allowed:
        return feature_disallowed(request, title, reason)

    c = {}

    def mk_verse_list(ref_list, verse_dict):
        verses = []
        for ref in ref_list: # preserve order
            if ref in verse_dict:
                verses.append(verse_dict[ref])
        return verses


    c['set_type'] = VerseSetType.name_for_value[set_type]

    if request.method == 'POST':
        orig_verse_set_public = False if verse_set is None else verse_set.public

        form = VerseSetForm(request.POST, instance=verse_set)
        # Need to propagate the references even if it doesn't validate,
        # so do this work here:
        ref_list_raw = request.POST.get('reference-list', '').split('|')
        verse_dict = version.get_verses_by_reference_bulk(ref_list_raw)
        # Dedupe ref_list, and ensure correct references, while preserving order:
        ref_list = []
        for ref in ref_list_raw:
            if ref in verse_dict and ref not in ref_list:
                ref_list.append(ref)

        breaks = request.POST.get('break-list', '')
        # Basic sanitising of 'breaks'
        if not re.match('^((\d+|\d+:\d+),)*(\d+|\d+:\d+)?$', breaks):
            breaks = ""

        form_is_valid = form.is_valid()
        if len(verse_dict) == 0:
            form.errors.setdefault('__all__', form.error_class()).append("No verses in set")
            form_is_valid = False

        if form_is_valid:
            verse_set = form.save(commit=False)
            verse_set.set_type = set_type
            verse_set.created_by = request.identity.account
            verse_set.breaks = breaks

            if orig_verse_set_public:
                # Can't undo:
                verse_set.public = True
            verse_set.save()
            verse_set.set_verse_choices(ref_list)

            # if user just made it public or it is a new public verse set
            if (verse_set.public and (orig_verse_set_public == False
                                      or mode == 'create'
                                      )):
                public_verse_set_created.send(sender=verse_set)

            messages.info(request, "Verse set '%s' saved!" % verse_set.name)
            return HttpResponseRedirect(reverse('view_verse_set', kwargs=dict(slug=verse_set.slug)))

    else:
        form = VerseSetForm(instance=verse_set)

        if verse_set is not None:
            ref_list = [vc.reference for vc in verse_set.verse_choices.all()]
            verse_dict = version.get_verses_by_reference_bulk(ref_list)
            breaks = verse_set.breaks
        else:
            ref_list, verse_dict, breaks = [], {}, ''

    verse_list = mk_verse_list(ref_list, verse_dict)
    if set_type == VerseSetType.PASSAGE:
        verse_list = add_passage_breaks(verse_list, breaks)

    c['verses'] = verse_list
    c['new_verse_set'] = verse_set == None
    c['verse_set_form'] = form
    c['title'] = title

    c.update(context_for_quick_find(request))

    return render(request, 'learnscripture/create_set.html', c)


def leaderboard(request):
    page_num = None # 1-indexed page page
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


    group = None
    if 'group' in request.GET:
        try:
            group = Group.objects.get(id=int(request.GET['group']))
        except (Group.DoesNotExist, ValueError):
            pass


    if thisweek:
        accounts = get_leaderboard_since(cutoff, page_num - 1, PAGE_SIZE, group=group)
    else:
        accounts = get_all_time_leaderboard(page_num - 1, PAGE_SIZE, group=group)


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
        account_dict['num_verses'] = verse_counts.get(identity.id, 0)
        account_dict['username'] = identity.account.username

    c = {}
    c['include_referral_links'] = True
    c['accounts'] = accounts
    c['title'] = u"Leaderboard"
    c['thisweek'] = thisweek
    c['page_num'] = page_num
    c['previous_page_num'] = page_num - 1
    c['next_page_num'] = page_num + 1
    c['PAGE_SIZE'] = PAGE_SIZE
    c['group'] = group
    return render(request, 'learnscripture/leaderboard.html', c)


def user_stats(request, username):
    account = get_object_or_404(Account.objects.active()
                                .select_related('total_score', 'identity'),
                                username=username)
    c = {'account': account,
         'title': account.username,
         'awards': account.visible_awards(),
         'include_referral_links': True,
         }
    one_week_ago = timezone.now() - timedelta(7)
    verses_started =  account.identity.verse_statuses_started()

    c['verses_started_all_time'] = verses_started.count()
    c['verses_started_this_week'] = verses_started.filter(first_seen__gte=one_week_ago).count()
    verses_finished =  verses_started.filter(strength__gte=memorymodel.LEARNT)
    c['verses_finished_all_time'] = verses_finished.count()
    c['verses_finished_this_week'] = verses_finished.filter(last_tested__gte=one_week_ago).count()
    c['verse_sets_created_all_time'] = account.verse_sets_created.count()
    c['verse_sets_created_this_week'] = account.verse_sets_created.filter(date_added__gte=one_week_ago).count()
    current_account = account_from_request(request)
    if current_account is not None and current_account == account:
        c['groups'] = account.get_groups()
    else:
        c['groups'] = account.get_public_groups()
    return render(request, 'learnscripture/user_stats.html', c)


@require_identity
def user_verses(request):
    identity = request.identity
    c = {'title': 'Progress'}
    verses = identity.verse_statuses_started().select_related('version')

    if 'bibleorder' in request.GET:
        c['bibleorder'] = True
        verses = verses.order_by('text_order', 'strength')
    else:
        verses = verses.order_by('strength', 'reference')
    c['verses'] = verses
    return render(request, 'learnscripture/user_verses.html', c)


@require_identity
def user_verse_sets(request):
    identity = request.identity
    c = {'title': u'Verse sets',
         'verse_sets_learning': identity.verse_sets_chosen(),
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
                  {'title': u'Password reset started'})

def password_reset_complete(request):
    return render(request, 'learnscripture/password_reset_complete.html',
                  {'title': u'Password reset complete'})



# Large copy and paste from django.contrib.auth.views, followed by customisations.
@sensitive_post_parameters()
@never_cache
def password_reset_confirm(request, uidb36=None, token=None):
    """
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    token_generator = default_token_generator
    set_password_form = AccountSetPasswordForm
    assert uidb36 is not None and token is not None # checked by URLconf
    post_reset_redirect = reverse('password_reset_complete')
    try:
        uid_int = base36_to_int(uidb36)
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
                            {'form':form,
                             'title': u"Account details"})


def date_to_js_ts(d):
    """
    Converts a date object to the timestamp required by the flot library
    """
    return int(d.strftime('%s'))*1000


def stats(request):
    from app_metrics.models import MetricDay

    def build_data(metric_slugs):
        metrics = (MetricDay.objects.filter(metric__slug__in=metric_slugs)
                   .select_related('metric'))

        # Missing metrics => zero. However, if we omit a value for a day, then the
        # plotting library interpolates, when we want it to say zero.  So we have to
        # build a dictionary of all values and loop through by day.

        min_date = None
        max_date = None

        grouped = {}
        for m in metrics:
            if min_date is None or m.created < min_date:
                min_date = m.created
            if max_date is None or m.created > max_date:
                max_date = m.created
            grouped[(m.metric.slug, m.created)] = m.num

        output_rows = dict((s, []) for s in metric_slugs)
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

    # Build cumulative stats from 'account_data'
    all_accounts = []
    new_accounts = account_data['new_account']
    total = 0
    for ts, c in new_accounts:
        total += c
        all_accounts.append((ts, total))
    account_data['all_accounts'] = all_accounts

    if 'requests' in request.GET:
        request_data = build_data(['request_all', 'request_html', 'request_json'])
        # request_other = request_total - request_html - request_json
        request_data['request_other'] = [(r_a[0], r_a[1] - r_h[1] - r_j[1]) for r_a, r_h, r_j in
                                         zip(request_data['request_all'],
                                             request_data['request_html'],
                                             request_data['request_json'])]
    else:
        request_data = None

    return render(request, 'learnscripture/stats.html',
                  {'title': 'Stats',
                   'verses_data': verses_data,
                   'request_data': request_data,
                   'account_data': account_data,
                   })


def natural_list(l):
    if len(l) == 0:
        return u''
    if len(l) == 1:
        return l[0]
    return u"%s and %s" % (u", ".join(l[0:-1]), l[-1])


def get_started_verses_count(identity):
    return identity.verse_statuses_started().count()


def donation_paypal_dict(account, url_start):
    return {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "item_name": u"Donation to LearnScripture.net",
        "invoice": "account-%s-%s" % (account.id,
                                      timezone.now()), # We don't need this, but must be unique
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


@require_account
def donate(request):
    identity = request.identity
    account = identity.account
    c = {'title': 'Donate'}

    url_start = paypal_url_start_for_request(request)

    paypal_dict = donation_paypal_dict(account, url_start)
    form = PayPalPaymentsForm(initial=paypal_dict)
    # render 'amount' as visible widget
    c['PRODUCTION'] = settings.LIVEBOX and settings.PRODUCTION
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
        referral_link = account.make_referral_link('http://%s/' % Site.objects.get_current().domain)
    else:
        referral_link = None

    return render(request, 'learnscripture/referral_program.html',
                  {'title': 'Referral program',
                   'referral_link': referral_link,
                   'include_referral_links': True,
                   })


def awards(request):
    awards = [AwardType.classes[t](level=AnyLevel) for t in AwardType.values]
    discovered_awards = []
    hidden_awards = []
    for award in awards:
        if award.highest_level() is None:
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
    award = AwardType.classes[award_type](level=AnyLevel)

    levels = []
    for level in range(award.max_level, 0, -1):
        awards = Award.objects.filter(award_type=award_type,
                                      level=level)
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
    groups = groups_visible_for_request(request).order_by('name')
    if 'q' in request.GET:
        q = request.GET['q']
        groups = (groups.filter(name__icontains=q) |
                  groups.filter(description__icontains=q)
                  )
    return render(request, 'learnscripture/groups.html', {'title': 'Groups',
                                                          'groups': groups,
                                                          })


def group(request, slug):
    groups = groups_visible_for_request(request).filter(slug=slug)
    group = get_object_or_404(groups)
    account = account_from_request(request)

    if account is not None and request.method == 'POST':
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
                   })


def create_group(request):
    return create_or_edit_group(request)


def edit_group(request, slug):
    return create_or_edit_group(request, slug=slug)


def create_or_edit_group(request, slug=None):
    account = account_from_request(request)
    if slug is not None:
        groups = groups_editable_for_request(request).filter(slug=slug)
        group = get_object_or_404(groups)
        mode = 'edit'
        title = u'Edit group: %s' % group.name
        initial = {'invited_users': group.invited_users()}
    else:
        group = None
        mode = 'create'
        title = u"Create group"
        initial = {}

    allowed, reason = auth.check_allowed(request, auth.Feature.CREATE_GROUP)
    if not allowed:
        return feature_disallowed(request, title, reason)


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
            orig_invited_users = set(group.invited_users())
            invited_users = set(form.cleaned_data['invited_users'])
            new_users = invited_users - orig_invited_users
            removed_users = orig_invited_users - invited_users

            group.invitations.filter(account__in=removed_users).delete()
            for u in new_users:
                group.invitations.create(account=u,
                                         created_by=account)

            messages.info(request, u"Group details saved.")
            return HttpResponseRedirect(reverse('group', args=(group.slug,)))
    else:
        form = EditGroupForm(instance=group, initial=initial)

    return render(request, 'learnscripture/edit_group.html',
                  {'title': title,
                   'group': group,
                   'form': form,
                   })


def group_select_list(request):
    groups = list(groups_visible_for_request(request))
    account = account_from_request(request)
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
        initial = {'name': account.first_name + u' ' + account.last_name,
                   'email': account.email }
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
                      body=\
"""
From: %(name)s
Email: %(email)s
Account: %(account)s
Message:

%(message)s
""" % {
            'name': contact_form.cleaned_data['name'],
            'email': email,
            'account': account.username if account is not None else '',
            'message': contact_form.cleaned_data['message'],
},
                      from_email=settings.SERVER_EMAIL,
                      to=[settings.CONTACT_EMAIL],
                      headers={'Reply-To': email} if email else {},
).send()
