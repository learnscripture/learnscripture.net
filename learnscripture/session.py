import logging

from datetime import datetime

from app_metrics.utils import metric
from django.core.urlresolvers import reverse
from django.utils import timezone

from accounts.models import Identity, Account
from learnscripture.datastructures import make_choices
from learnscripture.utils.logging import extra


LearningType = make_choices('LearningType',
                            [('revision', 'REVISION', 'Revision'),
                             ('learning', 'LEARNING', 'Learning'),
                             ('practice', 'PRACTICE', 'Practice'),
                             ])

# In the session we store a list of verses to look at.
#
# We store the order the verses should be looked at (which allows us to remove
# items from the list without confusion).
#
# We use the tuple (reference, verse_set_id) as an ID.  We need VerseSet ID
# because we treat verses differently if they are part of a passage. By avoiding
# the specific UserVerseStatus id, we can cope with a change of version more
# easily.

def get_verse_statuses(request):
    learning_type = request.session.get('learning_type', None)
    # Need some backwards compat for existing sessions:
    if learning_type is None:
        if request.session.get('revision', False):
            learning_type = LearningType.LEARNING
        else:
            learning_type = LearningType.REVISION


    ids = _get_verse_status_ids(request)
    bulk_refs = list((verse_set_id, ref)
                     for order, ref, needs_testing_override, verse_set_id in ids)
    uvs_dict = request.identity.get_verse_statuses_bulk(bulk_refs)
    retval = []
    for order, ref, needs_testing_override, verse_set_id in ids:
        try:
            uvs = uvs_dict[verse_set_id, ref]
        except KeyError:
            continue
        uvs.learn_order = order
        if needs_testing_override is not None:
            uvs.needs_testing_override = needs_testing_override

        # Decorate UVS with learning_type and return_to because we need it in UI
        # (learn.js), even though the latter doesn't really belong here
        uvs.learning_type = learning_type
        uvs.return_to = request.session.get('return_to', reverse('dashboard'))
        retval.append(uvs)
    return retval


def _get_verse_status_ids(request):
    return request.session.get('verses_to_learn', [])


def _save_verse_status_ids(request, ids):
    request.session['verses_to_learn'] = ids


def _set_learning_session_start(request, dt):
    request.session['learning_start'] = dt.strftime("%s")


def get_learning_session_start(request):
    return datetime.utcfromtimestamp(int(request.session['learning_start']))\
        .replace(tzinfo=timezone.utc)


def _set_verse_statuses(request, user_verse_statuses):
    _save_verse_status_ids(request,
                           [(order, uvs.reference, getattr(uvs, 'needs_testing_override', None), uvs.verse_set_id)
                            for order, uvs in enumerate(user_verse_statuses)])


def start_learning_session(request, user_verse_statuses, learning_type, return_to):
    _set_verse_statuses(request, user_verse_statuses)
    _set_learning_session_start(request, timezone.now())
    request.session['learning_type'] = learning_type
    request.session['score_logs'] = []
    request.session['verses_skipped'] = False
    request.session['return_to'] = return_to


def verse_status_finished(request, reference, verse_set_id, new_score_logs):
    _remove_user_verse_status(request, reference, verse_set_id)

    if (request.session.get('revision', False)     # compat for sessions in progress
        or request.session.get('learning_type', LearningType.PRACTICE) == LearningType.REVISION):
        score_log_ids = list(request.session['score_logs'])
        score_log_ids.extend([sl.id for sl in new_score_logs])
        request.session['score_logs'] = score_log_ids
        if len(_get_verse_status_ids(request)) == 0:
            if not request.session['verses_skipped']:
                request.identity.award_revision_complete_bonus(score_log_ids)
                # Ensure we switch to 'not revision', so that we can't get super
                # bonus more than once.
                request.session['revision'] = False # compat for existing sessions
                request.session['learning_type'] = LearningType.PRACTICE


def verse_status_skipped(request, reference, verse_set_id):
    request.session['verses_skipped'] = True
    return _remove_user_verse_status(request, reference, verse_set_id)


def verse_status_cancelled(request, reference, verse_set_id):
    return _remove_user_verse_status(request, reference, verse_set_id)


def _remove_user_verse_status(request, reference, verse_set_id):
    # We remove all that appear before reference, since we know that they will
    # be processed in order client side, and otherwise we potentially have race
    # conditions if the user presses 'next' or 'skip' multiple times quickly.
    ids = _get_verse_status_ids(request)
    new_ids = []
    found_ref = False
    for (order, ref, needs_testing_override, vs_id) in ids:
        if found_ref:
            new_ids.append((order, ref, needs_testing_override, vs_id))
        if (ref, vs_id) == (reference, verse_set_id):
            found_ref = True

    if not found_ref:
        # Presumably an error, or an old request arriving very late, so ignore
        new_ids = ids

    _save_verse_status_ids(request, new_ids)


def get_identity(request):
    identity = None
    identity_id = request.session.get('identity_id', None)
    if identity_id is not None:
        try:
            identity = Identity.objects.get(id=identity_id)
            if identity.expired:
                return None
            else:
                return identity
        except Identity.DoesNotExist:
            return None
    else:
        return None


def start_identity(request):
    referrer = None
    referrer_username = request.session.get('referrer_username', None)
    if referrer_username is not None:
        try:
            referrer = Account.objects.get(username=referrer_username)
        except Account.DoesNotExist:
            pass
    identity = Identity.objects.create(referred_by=referrer)
    set_identity(request, identity)
    metric('new_identity')
    return identity


def login(request, identity):
    set_identity(request, identity)
    metric('login')


def set_identity(request, identity):
    request.session['identity_id'] = identity.id


def logout(request):
    request.session['identity_id'] = None


def save_referrer(request):
    """
    Save referrer username from request (if any) to sesssion.
    """
    if 'from' in request.GET:
        request.session['referrer_username'] = request.GET['from']
