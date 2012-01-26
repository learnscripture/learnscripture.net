from piston.handler import BaseHandler
from piston.utils import rc

from bibleverses.models import UserVerseStatus, Verse
from learnscripture import session


class NextVerseHandler(BaseHandler):
    allowed_methods = ('GET',)
    model = UserVerseStatus
    fields = ('id', 'memory_stage', 'strength', 'first_seen', 'last_seen',
              ('verse', ('reference', 'text')),
              ('version', ('short_name', 'slug')))

    def read(self, request):
        identity = session.get_identity(request)
        if identity is None:
            return rc.FORBIDDEN

        uvs_ids = session.get_verses_to_learn(request)
        if len(uvs_ids) == 0:
            return rc.NOT_FOUND

        try:
            return identity.verse_statuses.select_related('version', 'verse_choice').get(id=uvs_ids[0])
        except UserVerseStatus.DoesNotExist:
            return rc.NOT_FOUND
