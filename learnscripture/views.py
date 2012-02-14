from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.http import urlparse

from accounts.forms import PreferencesForm
from bibleverses.models import VerseSet, BibleVersion, BIBLE_BOOKS, InvalidVerseReference, parse_ref, MAX_VERSES_FOR_SINGLE_CHOICE, VerseChoice, VerseSetType
from learnscripture import session, auth
from bibleverses.forms import VerseSelector, VerseSetForm, PassageVerseSelector

from .decorators import require_identity, require_preferences


def home(request):
    return render(request, 'learnscripture/home.html')


@require_preferences
def learn(request):
    c = {'bible_versions': BibleVersion.objects.all()}
    return render(request, 'learnscripture/learn.html', c)


@require_identity
def preferences(request):
    if request.method == "POST":
        form = PreferencesForm(request.POST, instance=request.identity)
        if form.is_valid():
            form.save()
            messages.info(request, "Prefences updated, thank you.")
            return get_next(request, reverse('start'))
    else:
        form = PreferencesForm(instance=request.identity)
    c = {'form':form}
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


@require_identity
def start(request):
    identity = request.identity
    if not identity.verse_statuses.exists():
        # The only possible thing is to choose some verses
        return HttpResponseRedirect(reverse('choose'))

    if request.method == 'POST':
        if 'learnqueue' in request.POST:
            session.set_verse_statuses(request, identity.verse_statuses_for_learning())
            return HttpResponseRedirect(reverse('learn'))
        if 'revisequeue' in request.POST:
            session.set_verse_statuses(request, identity.verse_statuses_for_revising())
            return HttpResponseRedirect(reverse('learn'))

    c = {'new_verses_queue': identity.verse_statuses_for_learning(),
         'revise_verses_queue': identity.verse_statuses_for_revising(),
         }
    return render(request, 'learnscripture/start.html', c)


@require_preferences
def choose(request):
    """
    Choose a verse or verse set
    """
    def learn_set(l):
        session.prepend_verse_statuses(request, l)
        return HttpResponseRedirect(reverse('learn'))

    if request.method == "POST":
        # Handle choose set
        vs_id = request.POST.get('verseset_id', None)
        if vs_id is not None:
            try:
                vs = VerseSet.objects.prefetch_related('verse_choices').get(id=vs_id)
            except VerseSet.DoesNotExist:
                # Shouldn't be possible by clicking on buttons.
                pass
            if vs is not None:
                return learn_set(request.identity.add_verse_set(vs))

        ref = request.POST.get('reference', None)
        if ref is not None:
            # First ensure it is valid
            try:
                parse_ref(ref, request.identity.default_bible_version,
                          max_length=MAX_VERSES_FOR_SINGLE_CHOICE)
            except InvalidVerseReference:
                pass # Ignore the post.
            else:
                vc, n = VerseChoice.objects.get_or_create(reference=ref,
                                                          verse_set=None)
                return learn_set([request.identity.add_verse_choice(vc)])

    c = {}
    verse_sets = VerseSet.objects.all().order_by('name').prefetch_related('verse_choices')
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
            try:
                verse_list = parse_ref(reference, request.identity.default_bible_version,
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


@require_preferences
def view_verse_set(request, slug):
    c = {}
    verse_set = get_object_or_404(VerseSet, slug=slug)
    # Decorate the verse choices with the text.

    version = request.identity.default_bible_version
    verse_choices = list(verse_set.verse_choices.all())
    verses = version.get_verses_by_reference_bulk([vc.reference for vc in verse_choices])
    for vc in verse_choices:
        vc.verse = verses[vc.reference]

    c['verse_set'] = verse_set
    c['verse_choices'] = verse_choices
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

        ref_list = refs.split('|')
        verse_dict = version.get_text_by_reference_bulk(ref_list)

        if form.is_valid():
            verse_set = form.save(commit=False)
            verse_set.set_type = verse_set_type
            verse_set.created_by = request.identity.account
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

            # Need to orphan the unused verse choices, because there
            # may be UserVerseStatus objects pointing to them already.
            for vc in old_vcs:
                vc.verse_set = None
                vc.save()

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
