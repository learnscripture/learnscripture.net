
from datetime import timedelta

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.http import urlparse
from django.utils import timezone

from accounts.forms import PreferencesForm
from bibleverses.models import VerseSet, BibleVersion, BIBLE_BOOKS, InvalidVerseReference, MAX_VERSES_FOR_SINGLE_CHOICE, VerseChoice, VerseSetType
from learnscripture import session, auth
from bibleverses.forms import VerseSelector, VerseSetForm, PassageVerseSelector

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
@require_identity
def start(request):

    identity = request.identity
    if not identity.verse_statuses.exists():
        # The only possible thing is to choose some verses
        return HttpResponseRedirect(reverse('choose'))

    if request.method == 'POST':
        if 'learnqueue' in request.POST:
            return learn_set(request, identity.verse_statuses_for_learning(), False)
        if 'revisequeue' in request.POST:
            return learn_set(request, identity.verse_statuses_for_revising(), True)
        if 'learnpassage' in request.POST:
            vs_id = int(request.POST['verse_set_id'])
            return learn_set(request, identity.verse_statuses_for_passage(vs_id), False)
        if 'revisepassage' in request.POST:
            vs_id = int(request.POST['verse_set_id'])
            return learn_set(request, identity.verse_statuses_for_passage(vs_id), True)
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


# No 'require_preferences' or 'require_identity' so that bots can browse this
# page and the linked pages unhindered, for SEO.

def choose(request):
    """
    Choose a verse or verse set
    """
    if request.method == "POST":
        if not has_preferences(request):
            # Shouldn't get here if UI preferences javascript is working right.
            return redirect_via_prefs(request)

        identity = request.identity
        version = None
        try:
            version = BibleVersion.objects.get(slug=request.POST['version_slug'])
        except KeyError, BibleVersion.DoesNotExist:
            version = identity.default_bible_version

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

    if 'q' in request.GET:
        verse_sets = verse_sets.filter(name__icontains=request.GET['q'])

    if 'new' in request.GET:
        verse_sets = verse_sets.order_by('-date_added')
    else: # popular, the default
        verse_sets = verse_sets.order_by('-popularity')
    c['verse_sets'] = verse_sets

    if 'lookup' in request.GET:
        c['active_tab'] = 'individual'
        verse_form = VerseSelector(request.GET)
        if verse_form.is_valid():
            reference = verse_form.make_reference()
            c['reference'] = reference

            if has_preferences(request):
                version = request.identity.default_bible_version
            else:
                version = get_default_bible_version()

            try:
                verse_list = version.get_verse_list(reference,
                                                    max_length=MAX_VERSES_FOR_SINGLE_CHOICE)
            except InvalidVerseReference as e:
                c['individual_search_msg'] = e.message
            else:
                c['individual_search_results'] = verse_list
    else:
        verse_form = VerseSelector()
        c['active_tab'] = 'verseset'

    c['verse_form'] = verse_form

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


def view_verse_set(request, slug):
    c = {}
    verse_set = get_object_or_404(verse_sets_visible_for_request(request), slug=slug)

    version = None
    try:
        version = BibleVersion.objects.get(slug=request.GET['version'])
    except KeyError, BibleVersion.DoesNotExist:
        pass

    if version is None:
        if hasattr(request, 'identity') and request.identity.default_bible_version is not None:
            version = request.identity.default_bible_version
        else:
            version = get_default_bible_version()

    # Decorate the verse choices with the text.
    verse_choices = list(verse_set.verse_choices.all())
    verses = version.get_verses_by_reference_bulk([vc.reference for vc in verse_choices])
    for vc in verse_choices:
        vc.verse = verses[vc.reference]

    c['verse_set'] = verse_set
    c['verse_choices'] = verse_choices
    c['version'] = version
    c['bible_versions'] = bible_versions_for_request(request)
    return render(request, 'learnscripture/single_verse_set.html', c)


@require_preferences
def create_set(request, slug=None):
    version = request.identity.default_bible_version

    if slug is not None:
        verse_set = get_object_or_404(request.identity.account.verse_sets_created.filter(slug=slug))
    else:
        verse_set = None

    allowed, reason = auth.check_allowed(request, auth.Feature.CREATE_VERSE_SET)
    if not allowed:
        return render(request, 'learnscripture/create_set.html',
                      {'barred': True,
                       'reason': reason,
                       'new_verse_set': verse_set == None})


    c = {}

    def mk_verse_list(ref_list, verse_dict):
        verses = []
        for ref in ref_list: # preserve order
            if ref in verse_dict:
                verses.append(dict(reference=ref, text=verse_dict[ref]))
        return verses


    if verse_set is None:
        if 'passage' in request.GET:
            c['active_tab'] = 'passage'
        else:
            c['active_tab'] = 'selection' # The default.
    else:
        if verse_set.set_type == VerseSetType.SELECTION:
            c['active_tab'] = 'selection'
        else:
            c['active_tab'] = 'passage'

    if request.method == 'POST':
        verse_set_type = None
        if verse_set is not None:
            verse_set_type = verse_set.set_type

        if verse_set_type is None:
            if 'selection-save' in request.POST:
                verse_set_type = VerseSetType.SELECTION
            else:
                verse_set_type = VerseSetType.PASSAGE

        assert verse_set_type is not None

        orig_verse_set_public = False if verse_set is None else verse_set.public

        selection_form = VerseSetForm(request.POST, instance=verse_set, prefix='selection')
        passage_form = VerseSetForm(request.POST, instance=verse_set, prefix='passage')

        if verse_set_type == VerseSetType.SELECTION:
            form = selection_form
            # Need to propagate the references even if it doesn't validate,
            # so do this work here:
            refs = request.POST.get('selection-reference-list', '')
        else:
            form = passage_form
            refs = request.POST.get('passage-reference-list', '')

        ref_list_raw = refs.split('|')
        # Dedupe ref_list while preserving order:
        ref_list = []
        for ref in ref_list_raw:
            if ref not in ref_list:
                ref_list.append(ref)
        verse_dict = version.get_text_by_reference_bulk(ref_list)

        if form.is_valid():
            verse_set = form.save(commit=False)
            verse_set.set_type = verse_set_type
            verse_set.created_by = request.identity.account

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
            verse_list =  mk_verse_list(ref_list, verse_dict)
            if verse_set_type == VerseSetType.SELECTION:
                c['selection_verses'] = verse_list
            else:
                c['passage_verses'] = verse_list

    else:
        if verse_set is not None:
            if verse_set.set_type == VerseSetType.SELECTION:
                selection_form = VerseSetForm(instance=verse_set, prefix='selection')
                passage_form = None
            else:
                selection_form = None
                passage_form = VerseSetForm(instance=verse_set, prefix='passage')
        else:
            selection_form = VerseSetForm(instance=None, prefix='selection')
            passage_form = VerseSetForm(instance=None, prefix='passage')
        if verse_set is not None:
            ref_list = [vc.reference for vc in verse_set.verse_choices.all()]
            verse_list = mk_verse_list(ref_list, version.get_text_by_reference_bulk(ref_list))
            if verse_set.set_type == VerseSetType.SELECTION:
                c['selection_verses'] = verse_list
            else:
                c['passage_verses'] = verse_list

    c['new_verse_set'] = verse_set == None
    c['selection_verse_set_form'] = selection_form
    c['passage_verse_set_form'] = passage_form
    c['selection_verse_selector_form'] = VerseSelector(prefix='selection')
    c['passage_verse_selector_form'] = PassageVerseSelector(prefix='passage')
    return render(request, 'learnscripture/create_set.html', c)


def leaderboard(request):
    sql ="""
SELECT
  accounts_account.username,
  ts1.points,
  COUNT(ts2.account_id) as rank
FROM
  (scores_totalscore ts1 CROSS JOIN scores_totalscore ts2)
  INNER JOIN accounts_account on ts1.account_id = accounts_account.id
WHERE
  ts2.points >= ts1.points
GROUP BY ts1.account_id, ts1.points, accounts_account.username
ORDER BY rank
LIMIT %s
OFFSET %s
"""
    from django.db import connection
    cursor = connection.cursor()

    page_num = None # 1-indexed page page
    try:
        page_num = int(request.GET['p'])
    except KeyError, ValueError:
        page_num = 1

    PAGE_SIZE = 30
    offset = max(0, page_num - 1) * PAGE_SIZE

    cursor.execute(sql, [PAGE_SIZE, offset])

    accounts = dictfetchall(cursor)

    c = {}
    c['accounts'] = accounts
    c['page_num'] = page_num
    c['previous_page_num'] = page_num - 1
    c['next_page_num'] = page_num + 1
    return render(request, 'learnscripture/leaderboard.html', c)
    row = cursor.fetchone()

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]
