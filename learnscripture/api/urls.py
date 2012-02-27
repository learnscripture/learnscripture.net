
from django.conf.urls import url, patterns
from django.http import Http404
from piston.resource import Resource as BaseResource
from piston.utils import HttpStatusCode


from learnscripture.api.handlers import VersesToLearnHandler, ActionCompleteHandler, ChangeVersionHandler, SignUpHandler, LogInHandler, LogOutHandler, GetVerseForSelection, GetPassage, SetPreferences, SessionStats, SkipVerseHandler, CancelLearningVerseHandler


class Resource(BaseResource):
    # We need to enable CSRF protection by default, not disable
    def __init__(self, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', False)

    def error_handler(self, e, request, meth, em_format):
        # the masking of errors by the base class is extremely annoying for
        # debugging, whether in development or in production.
        if isinstance(e, (Http404, HttpStatusCode)):
            return super(Resource, self).error_handler(e, request, meth, em_format)
        else:
            raise

# These URLs are hardcoded into Javascript instead of using URL reversing
# somehow. That's OK, because if you want to change them, you should be adding
# to them first for the sake of Javascript that is already loaded into the
# browser, and then only remove the old one when you are sure no javascript will
# try to use it.
urlpatterns = patterns('',
                       url(r'^versestolearn/$', Resource(VersesToLearnHandler)),
                       url(r'^actioncomplete/$', Resource(ActionCompleteHandler)),
                       url(r'^changeversion/$', Resource(ChangeVersionHandler)),
                       url(r'^signup/$', Resource(SignUpHandler)),
                       url(r'^login/$', Resource(LogInHandler)),
                       url(r'^logout/$', Resource(LogOutHandler)),
                       url(r'^getverseforselection/$', Resource(GetVerseForSelection)),
                       url(r'^getpassage/$', Resource(GetPassage)),
                       url(r'^setpreferences/$', Resource(SetPreferences)),
                       url(r'^sessionstats/$', Resource(SessionStats)),
                       url(r'^skipverse/$', Resource(SkipVerseHandler)),
                       url(r'^cancellearningverse/$', Resource(CancelLearningVerseHandler)),
                       )

