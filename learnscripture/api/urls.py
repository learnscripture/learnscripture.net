
from django.conf.urls import url, patterns
from piston.resource import Resource as BaseResource

from learnscripture.api.handlers import NextVerseHandler, ActionCompleteHandler, ChangeVersionHandler, SignupHandler


class Resource(BaseResource):
    # We need to enable CSRF protection by default, not disable
    def __init__(self, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', False)


urlpatterns = patterns('',
                       url(r'^nextverse/$', Resource(NextVerseHandler)),
                       url(r'^actioncomplete/$', Resource(ActionCompleteHandler)),
                       url(r'^changeversion/$', Resource(ChangeVersionHandler)),
                       url(r'^signup/$', Resource(SignupHandler)),
                       )

