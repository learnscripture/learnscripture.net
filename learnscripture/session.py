from accounts.models import Identity


def prepend_verse_statuses(request, user_verse_statuses):
    s = request.session.get('verses_to_learn', [])
    s = [uvs.id for uvs in user_verse_statuses] + s
    request.session['verses_to_learn'] = s


def remove_user_verse_status(request, uvs_id):
    s = request.session.get('verses_to_learn', [])
    s = [u for u in s if u != uvs_id]
    request.session['verses_to_learn'] = s


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
    request.session['identity_id'] = identity.id
    return identity


def get_verses_to_learn(request):
    return request.session.get('verses_to_learn', [])
