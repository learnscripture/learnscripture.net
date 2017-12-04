
from datetime import datetime

from app_metrics.utils import metric
from django.urls import reverse
from django.utils import timezone

from accounts.models import Account, Identity
from learnscripture.datastructures import make_choices

# Also defined in learn.ts and Learn.elm
LearningType = make_choices('LearningType',
                            [('REVISION', 'Revision'),
                             ('LEARNING', 'Learning'),
                             ('PRACTICE', 'Practice'),
                             ])

# In the session we store a list of verses to look at.
#
# We store the order the verses should be looked at (which allows us to remove
# items from the list without confusion).
#
# We use the tuple (localized_reference, verse_set_id) as an ID.  We need VerseSet ID
# because we treat verses differently if they are part of a passage. By avoiding
# the specific UserVerseStatus id, we can cope with a change of version more
# easily.

# Batch for verse statuses to avoid really long JSON which can get truncated.
# See also learn.js
VERSE_STATUS_BATCH_SIZE = 10


def get_verse_statuses(request):
    learning_type = request.session.get('learning_type', None)
    # Need some backwards compat for existing sessions:
    if learning_type is None:
        if request.session.get('revision', False):
            learning_type = LearningType.LEARNING
        else:
            learning_type = LearningType.REVISION

    id_data = _get_verse_status_ids(request)

    if len(id_data) > 0:
        max_order_val = max(order for order, uvs_id, n in id_data)
    else:
        max_order_val = None

    # Filtering:
    seen = request.GET.get('seen', '').strip()
    if seen:
        # Don't send them things they already have
        seen_ids = set([int(x) for x in seen.split(',')])
    else:
        seen_ids = set()

    id_batch = [(order, uvs_id, n) for order, uvs_id, n in id_data if uvs_id not in seen_ids]

    # Batching:
    id_batch = id_batch[:VERSE_STATUS_BATCH_SIZE]

    bulk_ids = [uvs_id
                for order, uvs_id, needs_testing_override in id_batch]
    uvs_dict = request.identity.get_verse_statuses_bulk(bulk_ids)
    retval = []
    for order, uvs_id, needs_testing_override in id_batch:
        try:
            uvs = uvs_dict[uvs_id]
        except KeyError:
            continue
        uvs.learn_order = order
        uvs.max_order_val = max_order_val  # Stick the same value on all, for convenience
        if needs_testing_override is not None:
            uvs.needs_testing_override = needs_testing_override

        # Decorate UVS with learning_type and return_to because we need it in UI
        # (learn.ts), even though the latter doesn't really belong here
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
    # We enumerate at this point and assign an order.  This order ends up being
    # used as 'learn_order', and is used in the front end as an index into a
    # dictionary (not an array), because items can be expelled from the list
    # stored in the session.
    _save_verse_status_ids(request,
                           [(order, uvs.id, getattr(uvs, 'needs_testing_override', None))
                            for order, uvs in enumerate(user_verse_statuses)])


def start_learning_session(request, user_verse_statuses, learning_type, return_to):
    _set_verse_statuses(request, user_verse_statuses)
    _set_learning_session_start(request, timezone.now())
    request.session['learning_type'] = learning_type
    request.session['action_logs'] = []
    request.session['return_to'] = return_to


def verse_status_finished(request, uvs_id, new_action_logs):
    _remove_user_verse_status(request, uvs_id)

    if (new_action_logs and request.session.get('learning_type', LearningType.PRACTICE) == LearningType.REVISION):
        action_log_ids = list(request.session['action_logs'])
        action_log_ids.extend([sl.id for sl in new_action_logs])
        request.session['action_logs'] = action_log_ids


def verse_status_skipped(request, uvs_id):
    return _remove_user_verse_status(request, uvs_id)


def verse_status_cancelled(request, uvs_id):
    return _remove_user_verse_status(request, uvs_id)


def _remove_user_verse_status(request, u_id):
    # We remove all that appear before reference, since we know that they will
    # be processed in order client side, and otherwise we potentially have race
    # conditions if the user presses 'next' or 'skip' multiple times quickly.
    ids = _get_verse_status_ids(request)
    new_ids = []
    found_id = False
    for (order, uvs_id, needs_testing_override) in ids:
        if found_id:
            new_ids.append((order, uvs_id, needs_testing_override))
        if u_id == uvs_id:
            found_id = True

    if not found_id:
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
    set_identity(request.session, identity)
    metric('new_identity')
    return identity


def login(request, identity):
    set_identity(request.session, identity)
    metric('login')


def set_identity(session, identity):
    session['identity_id'] = identity.id


def save_referrer(request):
    """
    Save referrer username from request (if any) to sesssion.
    """
    if 'from' in request.GET:
        request.session['referrer_username'] = request.GET['from']
