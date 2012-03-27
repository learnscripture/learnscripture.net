from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', 'learnscripture.views.home', name='home'),
                       (r'^favicon\.ico/?$', 'django.views.generic.simple.redirect_to', {'url': '/static/img/favicon.png'}),
                       url(r'^dashboard/$', 'learnscripture.views.dashboard', name='dashboard'),
                       url(r'^choose/$', 'learnscripture.views.choose', name='choose'),
                       url(r'^verse-set/(?P<slug>[^/]+)/$', 'learnscripture.views.view_verse_set',
                           name='view_verse_set'),
                       url(r'^create-verse-set/$', 'learnscripture.views.create_set_menu', name='create_set_menu'),
                       url(r'^create-selection-set/$', 'learnscripture.views.create_selection_set', name='create_selection_set'),
                       url(r'^create-passage-set/$', 'learnscripture.views.create_passage_set', name='create_passage_set'),
                       url(r'^edit-verse-set/(?P<slug>[^/]+)/$', 'learnscripture.views.edit_set', name='edit_set'),
                       url(r'^learn/$', 'learnscripture.views.learn', name='learn'),
                       url(r'^preferences/$', 'learnscripture.views.preferences', name='preferences'),
                       url(r'^progress/$', 'learnscripture.views.user_verses', name='user_verses'),
                       url(r'^leaderboard/$', 'learnscripture.views.leaderboard', name='leaderboard'),
                       url(r'^user/(.*)/$', 'learnscripture.views.user_stats', name='user_stats'),
                       url(r'^login/$', 'learnscripture.views.login', name='login'),

                       url(r'^password-reset/$', 'learnscripture.views.password_reset_done', name='password_reset_done'),
                       url(r'^reset/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', 'learnscripture.views.password_reset_confirm', name='password_reset_confirm'),
                       url(r'^reset/complete/$', 'learnscripture.views.password_reset_complete', name='password_reset_complete'),
                       url(r'^account/$', 'learnscripture.views.account_details', name='account_details'),
                       url(r'^stats/$', 'learnscripture.views.stats', name='stats'),
                       url(r'^subscribe/$', 'learnscripture.views.subscribe', name='subscribe'),


                       (r'^admin/fiber/', include('fiber.admin_urls')),
                       (r'^api/v1/', include('fiber.api.urls')),
                       (r'^api/learnscripture/v1/', include('learnscripture.api.urls')),
                       (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('fiber',),}),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^robots.txt$',  'django.views.generic.simple.redirect_to', {'url': '/static/robots.txt'}),
                       (r'', 'fiber.views.page'),
)


if settings.DEBUG:
    urlpatterns = urlpatterns + patterns('',
                           url(r'^usermedia/(?P<path>.*)$', 'django.views.static.serve',
                               {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
                           )
