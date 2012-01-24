from piston.handler import BaseHandler
from piston.utils import rc

from bibleverses.models import UserVerseStatus, Verse
from learnscripture import session


class NextVerseHandler(BaseHandler):
    allowed_methods = ('GET',)
    model = UserVerseStatus
    fields = ['memory_stage', 'strength', 'first_seen', 'last_seen',
              'verse_reference', 'verse_text']

    def read(self, request):
        identity = session.get_identity(request)
        if identity is None:
            return rc.FORBIDDEN

        uvs_ids = session.get_verses_to_learn(request)
        if len(uvs_ids) == 0:
            return rc.NOT_FOUND

        try:
            uvs = identity.verse_statuses.select_related('version', 'verse').get(id=uvs_ids[0])
        except UserVerseStatus.DoesNotExist:
            return rc.NOT_FOUND

        # Decorate with some things we need
        uvs.verse_reference = uvs.verse.reference
        v = Verse.objects.get(version=uvs.version,
                              reference=uvs.verse_reference)
        uvs.verse_text = v.text
        return uvs
