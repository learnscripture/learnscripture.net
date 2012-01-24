
from django.conf.urls import url, patterns
from piston.resource import Resource

from learnscripture.api.handlers import NextVerseHandler

next_verse_handler = Resource(NextVerseHandler)

urlpatterns = patterns('',
                       url(r'^nextverse/$', next_verse_handler),
                       )

