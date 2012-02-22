
from django.conf.urls import url, patterns
from piston.resource import Resource as BaseResource

from learnscripture.api.handlers import NextVerseHandler, ActionCompleteHandler, ChangeVersionHandler, SignUpHandler, LogInHandler, LogOutHandler, GetVerseForSelection, GetPassage, SetPreferences, SessionStats


class Resource(BaseResource):
    # We need to enable CSRF protection by default, not disable
    def __init__(self, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', False)

    def error_handler(self, e, request, meth, em_format):
        if isinstance(e, TypeError):
            # the masking of TypeError by the base class, on the assumption of
            # bad signature is extremely annoying for debugging, whether
            # in development or in production.
            raise
        else:
            return super(Resource, self).error_handler(e, request, meth, em_format)

# These URLs are hardcoded into Javascript instead of using URL reversing
# somehow. That's OK, because if you want to change them, you should be adding
# to them first for the sake of Javascript that is already loaded into the
# browser, and then only remove the old one when you are sure no javascript will
# try to use it.
urlpatterns = patterns('',
                       url(r'^nextverse/$', Resource(NextVerseHandler)),
                       url(r'^actioncomplete/$', Resource(ActionCompleteHandler)),
                       url(r'^changeversion/$', Resource(ChangeVersionHandler)),
                       url(r'^signup/$', Resource(SignUpHandler)),
                       url(r'^login/$', Resource(LogInHandler)),
                       url(r'^logout/$', Resource(LogOutHandler)),
                       url(r'^getverseforselection/$', Resource(GetVerseForSelection)),
                       url(r'^getpassage/$', Resource(GetPassage)),
                       url(r'^setpreferences/$', Resource(SetPreferences)),
                       url(r'^sessionstats/$', Resource(SessionStats)),
                       )

