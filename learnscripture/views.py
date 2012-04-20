
from datetime import timedelta
from decimal import Decimal, ROUND_DOWN
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.http import urlparse, base36_to_int
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters

from paypal.standard.forms import PayPalPaymentsForm

from accounts import memorymodel
from accounts.models import Account, SubscriptionType
from accounts.forms import PreferencesForm, AccountDetailsForm
from learnscripture.forms import AccountSetPasswordForm
from bibleverses.models import VerseSet, BibleVersion, BIBLE_BOOKS, InvalidVerseReference, MAX_VERSES_FOR_SINGLE_CHOICE, VerseChoice, VerseSetType, get_passage_sections
from learnscripture import session, auth
from bibleverses.forms import VerseSetForm
from payments.models import Price
from payments.sign import sign_payment_info
from scores.models import get_all_time_leaderboard, get_leaderboard_since, ScoreReason

from .decorators import require_identity, require_preferences, has_preferences, redirect_via_prefs, require_account

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
    return HttpResponseRedirect(reverse('dashboard'))


def bible_versions_for_request(request):
    if hasattr(request, 'identity'):
        return request.identity.available_bible_versions()
    return BibleVersion.objects.filter(public=True)


@require_preferences
def learn(request):
    request.identity.prepare_for_learning()
    c = {'bible_versions': bible_versions_for_request(request),
         'title': u"Learn",
         }
    return render(request, 'learnscripture/learn.html', c)


@require_identity
def preferences(request):
    if request.method == "POST":
        form = PreferencesForm(request.POST, instance=request.identity)
        if form.is_valid():
            form.save()
            return get_next(request, reverse('dashboard'))
    else:
        form = PreferencesForm(instance=request.identity)
    c = {'form':form,
         'title': u'Preferences',
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
def dashboard(request):

    identity = getattr(request, 'identity', None)

    if settings.REQUIRE_SUBSCRIPTION:
        if identity is not None and identity.require_subscribe():
            return HttpResponseRedirect(reverse('subscribe'))

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
            return HttpResponseRedirect(reverse('dashboard'))
        if 'cancelpassage' in request.POST:
            vs_id = int(request.POST['verse_set_id'])
            identity.cancel_passage(vs_id)
            return HttpResponseRedirect(reverse('dashboard'))

    c = {'new_verses_queue': identity.verse_statuses_for_learning(),
         'revise_verses_queue': identity.verse_statuses_for_revising(),
         'passages_for_learning': identity.passages_for_learning(),
         'passages_for_revising': identity.passages_for_revising(),
         'next_verse_due': identity.next_verse_due(),
         'title': 'Dashboard',
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
    verse_set = get_object_or_404(verse_sets_visible_for_request(request), slug=slug)
    c = {'include_referral_links': verse_set.public}


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

        form = VerseSetForm(request.POST, instance=verse_set)
        # Need to propagate the references even if it doesn't validate,
        # so do this work here:
        refs = request.POST.get('reference-list', '')

        ref_list_raw = refs.split('|')
        # Dedupe ref_list while preserving order:
        ref_list = []
        for ref in ref_list_raw:
            if ref not in ref_list:
                ref_list.append(ref)
        verse_dict = version.get_verses_by_reference_bulk(ref_list)

        breaks = request.POST.get('break-list', '')
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
                    dirty = False
                    if ref in existing_vcs_dict:
                        vc = existing_vcs_dict[ref]
                        if vc.set_order != i:
                            vc.set_order = i
                            dirty = True
                        old_vcs.remove(vc)
                    else:
                        vc = VerseChoice(verse_set=verse_set,
                                         reference=ref,
                                         set_order=i)
                        dirty = True
                    if dirty:
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
            if set_type == VerseSetType.PASSAGE:
                verse_list = add_passage_breaks(verse_list, breaks)
            c['verses'] = verse_list

    else:
        form = VerseSetForm(instance=verse_set)

        if verse_set is not None:
            ref_list = [vc.reference for vc in verse_set.verse_choices.all()]
            verse_dict = version.get_verses_by_reference_bulk(ref_list)
            verse_list = mk_verse_list(ref_list, verse_dict)
            if verse_set.set_type == VerseSetType.PASSAGE:
                verse_list = add_passage_breaks(verse_list, verse_set.breaks)
            c['verses'] = verse_list

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

    PAGE_SIZE = 30

    if thisweek:
        accounts = get_leaderboard_since(timezone.now() - timedelta(7), page_num - 1, PAGE_SIZE)
    else:
        accounts = get_all_time_leaderboard(page_num - 1, PAGE_SIZE)

    c = {}
    c['accounts'] = accounts
    c['title'] = u"Leaderboard"
    c['thisweek'] = thisweek
    c['page_num'] = page_num
    c['previous_page_num'] = page_num - 1
    c['next_page_num'] = page_num + 1
    c['PAGE_SIZE'] = PAGE_SIZE
    return render(request, 'learnscripture/leaderboard.html', c)


def user_stats(request, username):
    account = get_object_or_404(Account.objects.select_related('total_score', 'identity'),
                                username=username)
    c = {'account': account,
         'title': account.username,
         }
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
    c = {'title': 'Progress'}
    verses = (identity.verse_statuses.filter(ignored=False,
                                             strength__gt=0,
                                             last_tested__isnull=False)
              .select_related('version')
              )

    if 'bibleorder' in request.GET:
        c['bibleorder'] = True
        verses = verses.order_by('bible_verse_number', 'strength')
    else:
        verses = verses.order_by('strength', 'reference')
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


@require_account
def account_details(request):
    if request.method == 'POST':
        form = AccountDetailsForm(request.POST, instance=request.identity.account)
        if form.is_valid():
            form.save()
            messages.info(request, "Account details updated, thank you")
            return HttpResponseRedirect(reverse('account_details'))
    else:
        form = AccountDetailsForm(instance=request.identity.account)

    return render(request, 'learnscripture/account_details.html',
                  {'form':form,
                   'title': u"Account details"})


def date_to_js_ts(d):
    """
    Converts a date object to the timestamp required by the flot library
    """
    return int(d.strftime('%s'))*1000


def get_scores_since(start, reasons):
    from learnscripture.utils.db import dictfetchall
    from django.db import connection

    sql = """
SELECT date_trunc('day', created) as day, reason, COUNT(id) as c FROM scores_scorelog
WHERE created > %s
AND reason IN %s
GROUP BY day, reason
ORDER BY day ASC
"""
    cursor = connection.cursor()
    cursor.execute(sql, [start, reasons])
    return dictfetchall(cursor)


def stats(request):
    # We can use score logs to get stats we want.
    start = (timezone.now() - timedelta(31)).date()
    reasons = (ScoreReason.VERSE_TESTED, ScoreReason.VERSE_REVISED)
    d = get_scores_since(start, reasons)

    # Some rows might be missing some days, so need to fill in with zeros,
    # otherwise charting fails. Get dict of vals we do have:
    rows_by_reason = dict((reason, dict((r['day'], r['c']) for r in d if r['reason'] == reason))
                          for reason in reasons)
    # empty dict waiting to be filled:
    complete_rows_by_reason = dict((reason, []) for reason in reasons)
    old_dt = None
    for row in d:
        dt = row['day']
        if dt == old_dt and old_dt is not None:
            continue
        for reason in reasons:
            row_dict = rows_by_reason[reason]
            output_row = complete_rows_by_reason[reason]
            val = row_dict.get(dt, 0) # get zero if SQL query returned no row.
            ts = date_to_js_ts(dt)
            output_row.append((ts, val))
        old_dt = dt

    return render(request, 'learnscripture/stats.html',
                  {'title': 'Stats',
                   'verses_initial_tests_per_day': complete_rows_by_reason[ScoreReason.VERSE_TESTED],
                   'verses_revision_tests_per_day': complete_rows_by_reason[ScoreReason.VERSE_REVISED]
                   })


def natural_list(l):
    if len(l) == 0:
        return u''
    if len(l) == 1:
        return l[0]
    return u"%s and %s" % (u", ".join(l[0:-1]), l[-1])


@require_account
def subscribe(request):
    identity = request.identity
    account = identity.account
    c = {'title': 'Subscribe'}
    if not account.payment_possible():
        # Shortcut, to avoid any processing
        return render(request, 'learnscripture/subscribe.html', c)

    c['payment_possible'] = True

    c['free_trial'] = account.subscription == SubscriptionType.FREE_TRIAL
    c['basic_account'] = account.subscription == SubscriptionType.BASIC

    payment_due_date = account.payment_due_date()
    if (payment_due_date is not None and payment_due_date < timezone.now()):
        c['payment_overdue'] = True
        if account.subscription == SubscriptionType.FREE_TRIAL:
            c['was_on_free_trial'] = True
            # Add info about how many verses they have learned.

            # Some of this logic should probably be in the model layer
            learning_verses = verse_count = identity.verse_statuses.filter(ignored=False)
            c['started_verses_count'] = learning_verses.filter(strength__gt=Decimal('0.0')).count()
            well_learnt = (learning_verses
                           .exclude(verse_set__set_type=VerseSetType.PASSAGE)
                           .filter(strength__gt=Decimal('0.65')).order_by('strength'))[0:3]

            c['well_learnt_verses'] = natural_list([uvs.reference for uvs in well_learnt])

        if request.method == 'POST' and 'downgrade' in request.POST:
            if account.subscription != SubscriptionType.BASIC:
                Account.objects.filter(id=account.id).update(subscription=SubscriptionType.BASIC)
                messages.info(request, "Account downgraded to 'Basic'")
            return HttpResponseRedirect(reverse('dashboard'))


    discount = account.subscription_discount()

    price_groups = Price.objects.current_prices()
    currencies = sorted([currency for currency, prices in price_groups],
                         key=lambda currency: currency.name)
    c['currencies'] = currencies
    c['price_groups'] = price_groups


    def decorate_with_discount(price):
        a = price.amount
        if discount != Decimal('0.00'):
            a = (a - discount * a).quantize(Decimal('0.1'), rounding=ROUND_DOWN).quantize(Decimal('0.01'))
            price.discounted = True
        price.amount_with_discount = a

    def decorate_with_savings(price, relative_to):
        if price.days == relative_to.days:
            price.savings = None
            return
        expected = relative_to.amount_with_discount * Decimal(1.0 * price.days / relative_to.days)
        price.savings = (expected - price.amount_with_discount).quantize(Decimal('0.01'), rounding=ROUND_DOWN)


    price_forms = []
    for currency, prices in price_groups:

        # Find the shortest period, so that we can calculate the relative
        # savings for longer periods.
        shortest = sorted(prices, key=lambda p:p.days)[0]

        for price in prices:
            decorate_with_discount(price)
            decorate_with_savings(price, shortest)
            domain = Site.objects.get_current().domain
            protocol = 'https' if request.is_secure() else 'http'
            amount = str(price.amount_with_discount)
            paypal_dict = {
                "business": settings.PAYPAL_RECEIVER_EMAIL,
                "amount": amount,
                "item_name": u"%s subscription on LearnScripture.net" % price.description,
                "invoice": "%s-%s" % (account.id,
                                      timezone.now()), # We don't need this, but must be unique
                "notify_url":  "%s://%s%s" % (protocol, domain, reverse('paypal-ipn')),
                "return_url": "%s://%s%s" % (protocol, domain, reverse('pay_done')),
                "cancel_return": "%s://%s%s" % (protocol, domain, reverse('pay_cancelled')),
                "custom": sign_payment_info(dict(account=account.id,
                                                 amount=amount,
                                                 price=price.id)),
                "currency_code": price.currency.name,
                "no_note": "1",
                "no_shipping": "1",
                }
            form = PayPalPaymentsForm(initial=paypal_dict)
            price_forms.append(("%s_%s" % (currency.name, price.id), form))
    c['PRODUCTION'] = settings.LIVEBOX and settings.PRODUCTION
    c['price_forms'] = price_forms

    if discount != Decimal('0.00'):
        c['discount'] = (discount * 100).quantize(Decimal('1'))

    return render(request, 'learnscripture/subscribe.html', c)


@csrf_exempt
def pay_done(request):
    identity = getattr(request, 'identity')
    if identity is not None:
        # This doesn't actually check if a payment was just received,
        # but it is good enough.
        if (identity.account is not None
            and identity.account.subscription == SubscriptionType.PAID_UP
            and identity.account.paid_until > timezone.now()):
            messages.info(request, 'Payment received, thank you!')
            return HttpResponseRedirect(reverse('dashboard'))

    return render(request, 'learnscripture/pay_done.html', {'title': "Payment complete"})


@csrf_exempt
def pay_cancelled(request):
    return render(request, 'learnscripture/pay_cancelled.html', {'title': "Payment cancelled"})


def referral_program(request):
    if hasattr(request, 'identity') and request.identity.account is not None:
        referral_link = request.identity.account.make_referral_link('http://%s/' % Site.objects.get_current().domain)
    else:
        referral_link = None

    return render(request, 'learnscripture/referral_program.html',
                  {'title': 'Referral program',
                   'referral_link': referral_link,
                   'include_referral_links': True,
                   })
