
from django.conf.urls import url, patterns
from piston.resource import Resource

from learnscripture.api.handlers import NextVerseHandler, ActionCompleteHandler

urlpatterns = patterns('',
                       url(r'^nextverse/$', Resource(NextVerseHandler)),
                       url(r'^actioncomplete/$', Resource(ActionCompleteHandler)),
                       )

