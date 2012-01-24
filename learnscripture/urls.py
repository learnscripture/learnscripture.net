from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^start/$', 'learnscripture.views.start', name='start'),
                       url(r'^choose/$', 'learnscripture.views.choose', name='choose'),
                       url(r'^learn/$', 'learnscripture.views.learn', name='learn'),
                       url(r'^preferences/$', 'learnscripture.views.preferences', name='preferences'),
                       (r'^admin/fiber/', include('fiber.admin_urls')),
                       (r'^api/v1/', include('fiber.api.urls')),
                       (r'^api/learnscripture/v1/', include('learnscripture.api.urls')),
                       (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('fiber',),}),
                       url(r'^admin/', include(admin.site.urls)),
                       (r'', 'fiber.views.page'),
)


if settings.DEBUG:
    urlpatterns = urlpatterns + patterns('',
                           url(r'^usermedia/(?P<path>.*)$', 'django.views.static.serve',
                               {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
                           )
