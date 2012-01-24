from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^learn/$', 'learnscripture.views.learn', name='learn'),
                       url(r'^admin/', include(admin.site.urls)),
)


if settings.DEBUG:
    urlpatterns = urlpatterns + patterns('',
                           url(r'^usermedia/(?P<path>.*)$', 'django.views.static.serve',
                               {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
                           )
