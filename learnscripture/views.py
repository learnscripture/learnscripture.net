
from datetime import timedelta
import re

from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.http import urlparse, base36_to_int
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters


from accounts import memorymodel
from accounts.models import Account
from accounts.forms import PreferencesForm
from learnscripture.forms import AccountSetPasswordForm
from bibleverses.models import VerseSet, BibleVersion, BIBLE_BOOKS, InvalidVerseReference, MAX_VERSES_FOR_SINGLE_CHOICE, VerseChoice, VerseSetType, get_passage_sections
from learnscripture import session, auth
from bibleverses.forms import VerseSetForm
from scores.models import get_all_time_leaderboard, get_leaderboard_since

from .decorators import require_identity, require_preferences, has_preferences, redirect_via_prefs

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
    return render(request, 'learnscripture/home.html')


# See comment in accounts.js for why this required (and doesn't do any logging
# in).
def login(request):
    # Redirect to dashboard because just about everything you might want to do
    # will change after sign in, and we want to encourage people to do their
    # revision first.
    return HttpResponseRedirect(reverse('start'))


def bible_versions_for_request(request):
    if request.user.is_superuser:
        return BibleVersion.objects.all()
    else:
        return BibleVersion.objects.filter(public=True)


@require_preferences
def learn(request):
    request.identity.prepare_for_learning()
    c = {'bible_versions': bible_versions_for_request(request)}
    return render(request, 'learnscripture/learn.html', c)


@require_identity
def preferences(request):
    if request.method == "POST":
        form = PreferencesForm(request.POST, instance=request.identity)
        if form.is_valid():
            form.save()
            return get_next(request, reverse('start'))
    else:
        form = PreferencesForm(instance=request.identity)
    c = {'form':form,
         'hide_preferences_popup': True}
    return render(request, 'learnscripture/preferences.html', c)


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


def learn_set(request, uvs_list, revision):
    session.start_learning_session(request, uvs_list, revision)
    return HttpResponseRedirect(reverse('learn'))


# Dashboard:
def start(request):

    identity = getattr(request, 'identity', None)
    if identity is None or not identity.verse_statuses.exists():
        # The only possible thing is to choose some verses
        return HttpResponseRedirect(reverse('choose'))

    if request.method == 'POST':
        if 'learnqueue' in request.POST:
            return learn_set(request, identity.verse_statuses_for_learning(), False)
        if 'revisequeue' in request.POST:
            return learn_set(request, identity.verse_statuses_for_revising(), True)
        if ('learnpassage' in request.POST or
            'revisepassage' in request.POST or
            'revisepassagesection' in request.POST):

            vs_id = int(request.POST['verse_set_id'])
            verse_set = VerseSet.objects.get(id=vs_id)
            uvss = identity.verse_statuses_for_passage(vs_id)

            if 'learnpassage' in request.POST:
                uvss = identity.slim_passage_for_revising(uvss, verse_set)
                return learn_set(request, uvss, False)
            if 'revisepassage' in request.POST:
                uvss = identity.slim_passage_for_revising(uvss, verse_set)
                return learn_set(request, uvss, True)
            if 'revisepassagesection' in request.POST:
                uvss = identity.get_next_section(uvss, verse_set)
                return learn_set(request, uvss, True)

        if 'clearqueue' in request.POST:
            identity.clear_learning_queue()
            return HttpResponseRedirect(reverse('start'))
        if 'cancelpassage' in request.POST:
            vs_id = int(request.POST['verse_set_id'])
            identity.cancel_passage(vs_id)
            return HttpResponseRedirect(reverse('start'))

    c = {'new_verses_queue': identity.verse_statuses_for_learning(),
         'revise_verses_queue': identity.verse_statuses_for_revising(),
         'passages_for_learning': identity.passages_for_learning(),
         'passages_for_revising': identity.passages_for_revising(),
         }
    c.update(session_stats(identity))
    return render(request, 'learnscripture/start.html', c)


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
            version = BibleVersion.objects.get(slug=request.POST['version_slug'])
        except (KeyError, BibleVersion.DoesNotExist):
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
                return learn_set(request, identity.add_verse_set(vs, version=version), False)

        # Handle choose individual verse
        ref = request.POST.get('reference', None)
        if ref is not None:
            # First ensure it is valid
            try:
                version.get_verse_list(ref, max_length=MAX_VERSES_FOR_SINGLE_CHOICE)
            except InvalidVerseReference:
                pass # Ignore the post.
            else:
                return learn_set(request, [identity.add_verse_choice(ref, version=version)], False)

    c = {}
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


def get_default_bible_version():
    # Use NET as default version because:
    # - they let us use their version without royalties
    # - it is a modern readable version.
    return BibleVersion.objects.get(slug='NET')


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
    c = {}
    verse_set = get_object_or_404(verse_sets_visible_for_request(request), slug=slug)


    version = None
    try:
        version = BibleVersion.objects.get(slug=request.GET['version'])
    except (KeyError, BibleVersion.DoesNotExist):
        pass

    if version is None:
        if hasattr(request, 'identity') and request.identity.default_bible_version is not None:
            version = request.identity.default_bible_version
        else:
            version = get_default_bible_version()

    # Decorate the verse choices with the text.
    verse_choices = list(verse_set.verse_choices.all())
    verses = version.get_verses_by_reference_bulk([vc.reference for vc in verse_choices])

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
                messages.info(request, "Verse set converted to 'passage' type")
                c['show_convert_to_passage'] = False


    if hasattr(request, 'identity'):
        c['can_edit'] = verse_set.created_by_id == request.identity.account_id
    else:
        c['can_edit'] = False
    c['verse_set'] = verse_set
    c['verse_choices'] = verse_choices
    c['version'] = version
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
    return render(request, 'learnscripture/create_set_menu.html', {})


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
    else:
        verse_set = None

    allowed, reason = auth.check_allowed(request, auth.Feature.CREATE_VERSE_SET)
    if not allowed:
        return render(request, 'learnscripture/create_set_menu.html',
                      {'barred': True,
                       'reason': reason,
                       'new_verse_set': verse_set == None})


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

        if set_type == VerseSetType.SELECTION:
            form = VerseSetForm(request.POST, instance=verse_set, prefix='selection')
            # Need to propagate the references even if it doesn't validate,
            # so do this work here:
            refs = request.POST.get('selection-reference-list', '')
        else:
            form = VerseSetForm(request.POST, instance=verse_set, prefix='passage')
            refs = request.POST.get('passage-reference-list', '')

        ref_list_raw = refs.split('|')
        # Dedupe ref_list while preserving order:
        ref_list = []
        for ref in ref_list_raw:
            if ref not in ref_list:
                ref_list.append(ref)
        verse_dict = version.get_verses_by_reference_bulk(ref_list)

        breaks = request.POST.get('passage-break-list', '')
        # Basic sanitising of 'breaks'
        if not re.match('^((\d+|\d+:\d+),)*(\d+|\d+:\d+)?$', breaks):
            breaks = ""

        if form.is_valid():
            verse_set = form.save(commit=False)
            verse_set.set_type = set_type
            verse_set.created_by = request.identity.account
            verse_set.breaks = breaks

            if orig_verse_set_public:
                # Can't undo:
                verse_set.public = True
            verse_set.save()

            # Need to ensure that we preserve existing objects
            existing_vcs = verse_set.verse_choices.all()
            existing_vcs_dict = dict((vc.reference, vc) for vc in existing_vcs)
            old_vcs = set(existing_vcs)
            for i, ref in enumerate(ref_list):  # preserve order
                if ref in verse_dict:
                    if ref in existing_vcs_dict:
                        vc = existing_vcs_dict[ref]
                        vc.set_order=i
                        old_vcs.remove(vc)
                    else:
                        vc = VerseChoice(verse_set=verse_set,
                                         reference=ref,
                                         set_order=i)
                    vc.save()
                else:
                    # If not in verse_dict, it can only be because user fiddled
                    # with the DOM.
                    pass

            # Delete unused VerseChoice objects.
            for vc in old_vcs:
                vc.delete()

            messages.info(request, "Verse set '%s' saved!" % verse_set.name)
            return HttpResponseRedirect(reverse('view_verse_set', kwargs=dict(slug=verse_set.slug)))
        else:
            # Invalid forms
            verse_list =  mk_verse_list(ref_list, verse_dict)
            if set_type == VerseSetType.SELECTION:
                c['selection_verses'] = verse_list
            else:
                c['passage_verses'] = add_passage_breaks(verse_list, breaks)

    else:
        if verse_set is not None:
            if set_type == VerseSetType.SELECTION:
                form = VerseSetForm(instance=verse_set, prefix='selection')
            else:
                form = VerseSetForm(instance=verse_set, prefix='passage')
        else:
            if set_type == VerseSetType.SELECTION:
                form = VerseSetForm(instance=None, prefix='selection')
            else:
                form = VerseSetForm(instance=None, prefix='passage')

        if verse_set is not None:
            ref_list = [vc.reference for vc in verse_set.verse_choices.all()]
            verse_dict = version.get_verses_by_reference_bulk(ref_list)
            verse_list = mk_verse_list(ref_list, verse_dict)
            if verse_set.set_type == VerseSetType.SELECTION:
                c['selection_verses'] = verse_list
            else:
                c['passage_verses'] = add_passage_breaks(verse_list, verse_set.breaks)

    c['new_verse_set'] = verse_set == None
    c['verse_set_form'] = form
    c['title'] = ('Edit verse set' if verse_set is not None
                  else 'Create selection set' if set_type == VerseSetType.SELECTION
                  else 'Create passage set')

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

    if thisweek:
        accounts = get_leaderboard_since(timezone.now() - timedelta(7), page_num - 1, 30)
        print accounts
    else:
        accounts = get_all_time_leaderboard(page_num - 1, 30)

    c = {}
    c['accounts'] = accounts
    c['thisweek'] = thisweek
    c['page_num'] = page_num
    c['previous_page_num'] = page_num - 1
    c['next_page_num'] = page_num + 1
    return render(request, 'learnscripture/leaderboard.html', c)


def user_stats(request, username):
    account = get_object_or_404(Account.objects.select_related('total_score', 'identity'),
                                username=username)
    c = {'account': account}
    one_week_ago = timezone.now() - timedelta(7)
    verses_started =  account.identity.verse_statuses.filter(ignored=False,
                                                             last_tested__isnull=False)

    c['verses_started_all_time'] = verses_started.count()
    c['verses_started_this_week'] = verses_started.filter(first_seen__gte=one_week_ago).count()
    verses_finished =  verses_started.filter(strength__gte=memorymodel.LEARNT)
    c['verses_finished_all_time'] = verses_finished.count()
    c['verses_finished_this_week'] = verses_finished.filter(last_tested__gte=one_week_ago).count()
    c['verse_sets_created_all_time'] = account.verse_sets_created.count()
    c['verse_sets_created_this_week'] = account.verse_sets_created.filter(date_added__gte=one_week_ago).count()
    return render(request, 'learnscripture/user_stats.html', c)


@require_identity
def user_verses(request):
    identity = request.identity
    verses = identity.verse_statuses.filter(ignored=False,
                                            strength__gt=0,
                                            last_tested__isnull=False)\
        .select_related('version').order_by('strength')

    c = {}
    c['verses'] = verses
    return render(request, 'learnscripture/user_verses.html', c)


# Password reset for Accounts:
#
# We can re-use a large amount of django.contrib.auth functionality
# due to same interface between Account and User. Some things need
# customising replacing.
#
# Also, we do the main password_reset via AJAX,
# from the the same form as the login form.

def password_reset_done(request):
    return render(request, 'learnscripture/password_reset_done.html', {})

def password_reset_complete(request):
    return render(request, 'learnscripture/password_reset_complete.html', {})



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
