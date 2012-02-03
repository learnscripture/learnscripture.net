from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import urlparse

from accounts.forms import PreferencesForm
from bibleverses.models import VerseSet, BibleVersion, BIBLE_BOOKS, InvalidVerseReference, parse_ref, MAX_VERSES_FOR_SINGLE_CHOICE, VerseChoice
from learnscripture import session

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
                verselist = parse_ref(ref, request.identity.default_bible_version,
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

    c['BIBLE_BOOKS'] = BIBLE_BOOKS

    if 'lookup_reference' in request.GET:
        c['active_tab'] = 'individual'
        book = request.GET.get('biblebook', '')
        reference_pt2 = request.GET.get('reference_pt2', '').strip()
        reference = book + ' ' + reference_pt2
        c['reference_pt2'] = reference_pt2
        c['reference'] = reference
        c['biblebook'] = request.GET.get('biblebook', '')
        try:
            verse_list = parse_ref(reference, request.identity.default_bible_version,
                                   max_length=MAX_VERSES_FOR_SINGLE_CHOICE)
        except InvalidVerseReference as e:
            c['individual_search_msg'] = u"The reference was not recognised: %s" % (e.message)
        else:
            c['individual_search_results'] = verse_list


    else:
        c['active_tab'] = 'verseset'

    return render(request, 'learnscripture/choose.html', c)
