import logging

from accounts.models import Identity
from learnscripture.utils.logging import extra

logger = logging.getLogger(__name__)


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
    ids = _get_verse_status_ids(request)
    bulk_refs = list((verse_set_id, ref) for order, ref, verse_set_id in ids)
    uvs_dict = request.identity.get_verse_statuses_bulk(bulk_refs)
    retval = []
    for order, ref, verse_set_id in ids:
        try:
            uvs = uvs_dict[verse_set_id, ref]
        except KeyError:
            continue
        uvs.learn_order = order
        retval.append(uvs)
    return retval

def _get_verse_status_ids(request):
    return request.session.get('verses_to_learn', [])


def _save_verse_status_ids(request, ids):
    request.session['verses_to_learn'] = ids


def set_verse_statuses(request, user_verse_statuses):
    _save_verse_status_ids(request,
                           [(order, uvs.reference, uvs.verse_choice.verse_set_id)
                            for order, uvs in enumerate(user_verse_statuses)])


def remove_user_verse_status(request, reference, verse_set_id):
    # TODO: Race condition possible here. Therefore should remove all that
    # appear before reference, since we know that they will be processed in
    # order client side.
    ids = _get_verse_status_ids(request)
    ids = [(order, ref, vs_id) for order, ref, vs_id in ids
           if (ref, vs_id) != (reference, verse_set_id)]
    _save_verse_status_ids(request, ids)


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
    identity = Identity.objects.create()
    logger.info("New Identity created", extra=extra(identity=identity, request=request))
    set_identity(request, identity)
    return identity


def login(request, identity):
    set_identity(request, identity)
    logger.info("Login", extra=extra(identity=identity, request=request))


def set_identity(request, identity):
    request.session['identity_id'] = identity.id


def logout(request):
    request.session['identity_id'] = None
