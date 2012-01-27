from django.utils.functional import wraps

from piston.handler import BaseHandler
from piston.utils import rc

from bibleverses.models import UserVerseStatus, Verse
from learnscripture import session

def require_identity(method):
    @wraps(method)
    def wrapper(self, request, *args, **kwargs):
        identity = session.get_identity(request)
        if identity is None:
            return rc.FORBIDDEN
        request.identity = identity
        return method(self, request, *args, **kwargs)
    return wrapper


class NextVerseHandler(BaseHandler):
    allowed_methods = ('GET',)
    model = UserVerseStatus
    fields = ('id', 'memory_stage', 'strength', 'first_seen', 'last_seen',
              ('verse_choice', (('verse_set', ('id',)),)),
              ('verse', ('reference', 'text')),
              ('version', ('full_name', 'short_name', 'slug', 'url')))

    @require_identity
    def read(self, request):
        uvs_ids = session.get_verses_to_learn(request)
        if len(uvs_ids) == 0:
            return rc.NOT_FOUND

        try:
            return request.identity.verse_statuses.select_related('version', 'verse_choice', 'verse_choice__verse_set').get(id=uvs_ids[0])
        except UserVerseStatus.DoesNotExist:
            return rc.NOT_FOUND


class ActionCompleteHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_identity
    def create(self, request):
        uvs_id = int(request.data['user_verse_status_id'])
        try:
            uvs = request.identity.verse_statuses.get(id=uvs_id)
        except UserVerseStatus.DoesNotExist:
            return rc.NOT_FOUND

        # TODO: store StageComplete
        # TODO: update UserVerseStatus
        if request.data['stage'] == 'test':
            session.remove_user_verse_status(request, uvs_id)

        return {}


class ChangeVersionHandler(BaseHandler):
    allowed_methods = ('POST',)

    @require_identity
    def create(self, request):
        verse_set_id = request.data['verse_set_id']
        if verse_set_id == '' or verse_set_id == 'null':
            verse_set_id = None
        else:
            verse_set_id = int(verse_set_id)

        reference = request.data['reference']
        version_slug = request.data['version_slug']
        request.identity.change_version(reference,
                                        version_slug,
                                        verse_set_id)
        session.remove_user_verse_status(request, int(request.data['user_verse_status_id']))
        uvs = request.identity.verse_statuses.get(verse_choice__verse_set=verse_set_id,
                                                  verse_choice__reference=reference,
                                                  version__slug=version_slug)
        session.prepend_verse_statuses(request, [uvs])

        return {}

