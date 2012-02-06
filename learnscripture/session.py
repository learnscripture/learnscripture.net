from accounts.models import Identity


def get_verse_statuses(request):
    return request.identity.verse_statuses.filter(id__in=get_verse_status_ids(request))


def get_verse_status_ids(request):
    return request.session.get('verses_to_learn', [])


def _save_verse_status_ids(request, ids):
    request.session['verses_to_learn'] = ids


def set_verse_statuses(request, user_verse_statuses):
    _save_verse_status_ids(request, [u.id for u  in user_verse_statuses])


def prepend_verse_statuses(request, user_verse_statuses):
    _save_verse_status_ids(request,
                           [uvs.id for uvs in user_verse_statuses] +
                           get_verse_status_ids(request))


def remove_user_verse_status_id(request, uvs_id):
    s = get_verse_status_ids(request)
    s = [u for u in s if u != uvs_id]
    _save_verse_status_ids(request, s)


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
    set_identity(request, identity)
    return identity


def set_identity(request, identity):
    request.session['identity_id'] = identity.id


def logout(request):
    request.session['identity_id'] = None
