import logging

from accounts.models import Identity
from learnscripture.utils.logging import extra

logger = logging.getLogger(__name__)


# In the session we store a list of verses to look at.  We use the tuple
# (reference, verse_set_id) as an ID.  We need to VerseSet ID because we treat
# verses differently if they are part of a passage. By avoiding the specific
# UserVerseStatus id, we can cope with a change of version more easily.


def _verse_status_info(uvs):
    return (uvs.reference, uvs.verse_choice.verse_set_id)


def get_next_verse_status(request):
    ids = _get_verse_status_ids(request)
    if len(ids) == 0:
        return None
    ref, verse_set_id = ids[0]
    return request.identity.get_verse_status_for_ref(ref, verse_set_id)


def _get_verse_status_ids(request):
    return request.session.get('verses_to_learn', [])


def _save_verse_status_ids(request, ids):
    request.session['verses_to_learn'] = ids


def set_verse_statuses(request, user_verse_statuses):
    _save_verse_status_ids(request, map(_verse_status_info, user_verse_statuses))


def remove_user_verse_status(request, reference, verse_set_id):
    ids = _get_verse_status_ids(request)
    ids = [i for i in ids if i != (reference, verse_set_id)]
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
