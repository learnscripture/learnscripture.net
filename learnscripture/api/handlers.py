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
              ('verse', ('reference', 'text')),
              ('version', ('short_name', 'slug')))

    @require_identity
    def read(self, request):
        uvs_ids = session.get_verses_to_learn(request)
        if len(uvs_ids) == 0:
            return rc.NOT_FOUND

        try:
            return request.identity.verse_statuses.select_related('version', 'verse_choice').get(id=uvs_ids[0])
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

        return rc.CREATED
