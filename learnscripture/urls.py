from django.conf import settings
from django.conf.urls import include, patterns, url
from django.contrib import admin
from django.views.generic import RedirectView

admin.autodiscover()

urlpatterns = patterns('',
                       # Home page
                       url(r'^$', 'learnscripture.views.home', name='home'),

                       # Static files
                       url(r'^robots.txt$', RedirectView.as_view(url='/static/robots.txt')),
                       url(r'^favicon\.ico/?$', RedirectView.as_view(url='/static/img/favicon.png')),

                       # Main views, different for each user
                       url(r'^dashboard/$', 'learnscripture.views.dashboard', name='dashboard'),
                       url(r'^choose/$', 'learnscripture.views.choose', name='choose'),
                       url(r'^catechisms/$', 'learnscripture.views.view_catechism_list', name='catechisms'),
                       url(r'^catechisms/(?P<slug>[^/]+)/$', 'learnscripture.views.view_catechism', name='view_catechism'),
                       url(r'^learn/$', 'learnscripture.views.learn', name='learn'),
                       url(r'^preferences/$', 'learnscripture.views.preferences', name='preferences'),
                       url(r'^progress/$', 'learnscripture.views.user_verses', name='user_verses'),
                       url(r'^my-verse-sets/$', 'learnscripture.views.user_verse_sets', name='user_verse_sets'),
                       url(r'^verse-options/$', 'learnscripture.views.verse_options', name='verse_options'),

                       # Payment
                       url(r'^donate/$', 'learnscripture.views.donate', name='donate'),
                       url(r'^donation-complete/$', 'learnscripture.views.pay_done', name='pay_done'),
                       url(r'^donation-cancelled/$', 'learnscripture.views.pay_cancelled', name='pay_cancelled'),

                       # Account management
                       url(r'^login/$', 'learnscripture.views.login', name='login'),
                       url(r'^signup/$', 'learnscripture.views.signup', name='signup'),
                       url(r'^account/$', 'learnscripture.views.account_details', name='account_details'),
                       url(r'^password-reset/$', 'learnscripture.views.password_reset_done', name='password_reset_done'),
                       url(r'^change-password/$', 'learnscripture.views.password_change', name='learnscripture_password_change'),
                       url(r'^change-password/done/$', 'learnscripture.views.password_change_done', name='learnscripture_password_change_done'),
                       url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$', 'learnscripture.views.password_reset_confirm', name='password_reset_confirm'),
                       url(r'^reset/complete/$', 'learnscripture.views.password_reset_complete', name='password_reset_complete'),
                       url(r'^login/$', 'learnscripture.views.login', name='admin_password_reset'),

                       # Verse sets
                       url(r'^verse-set/(?P<slug>[^/]+)/$', 'learnscripture.views.view_verse_set', name='view_verse_set'),
                       url(r'^create-verse-set/$', 'learnscripture.views.create_set_menu', name='create_set_menu'),
                       url(r'^create-selection-set/$', 'learnscripture.views.create_selection_set', name='create_selection_set'),
                       url(r'^create-passage-set/$', 'learnscripture.views.create_passage_set', name='create_passage_set'),
                       url(r'^edit-verse-set/(?P<slug>[^/]+)/$', 'learnscripture.views.edit_set', name='edit_set'),

                       # User stats
                       url(r'^user/([^/]*)/$', 'learnscripture.views.user_stats', name='user_stats'),
                       url(r'^user/(.*)/verses_timeline_stats.csv$', 'learnscripture.views.user_stats_verses_timeline_stats_csv', name='user_stats_verses_timeline_stats_csv'),

                       # Activity
                       url(r'^activity/$', 'learnscripture.views.activity_stream', name='activity_stream'),
                       url(r'^activity/(\d+)/$', 'learnscripture.views.activity_item', name='activity_item'),
                       url(r'^user/([^/]*)/activity/$', 'learnscripture.views.user_activity_stream', name='user_activity_stream'),

                       # Badges
                       url(r'^badges/$', 'learnscripture.views.awards', name='awards'),
                       url(r'^badges/(.*)/$', 'learnscripture.views.award', name='award'),

                       # Groups
                       url(r'^groups/$', 'learnscripture.views.groups', name='groups'),
                       url(r'^groups/([^/]*)/$', 'learnscripture.views.group', name='group'),
                       url(r'^groups/([^/]*)/wall/$', 'learnscripture.views.group_wall', name='group_wall'),
                       url(r'^groups/([^/]*)/leaderboard/$', 'learnscripture.views.group_leaderboard', name='group_leaderboard'),
                       url(r'^create-group/$', 'learnscripture.views.create_group', name='create_group'),
                       url(r'^edit-group/(.*)/$', 'learnscripture.views.edit_group', name='edit_group'),
                       url(r'^group-select-list/$', 'learnscripture.views.group_select_list', name='group_select_list'),

                       # Other
                       url(r'^contact/$', 'learnscripture.views.contact', name='contact'),
                       url(r'^terms-of-service/$', 'learnscripture.views.terms_of_service', name='terms_of_service'),
                       url(r'^referral-program/$', 'learnscripture.views.referral_program', name='referral_program'),


                       url(r'^stats/$', 'learnscripture.views.stats', name='stats'),

                       # JSON/AJAX views

                       url(r'^api/learnscripture/v1/', include('learnscripture.api.urls')),

                       # Dependencies
                       (r'^admin/fiber/', include('fiber.admin_urls')),
                       (r'^api/v2/', include('fiber.rest_api.urls')),
                       (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ['fiber']}),
                       url(r'^admin/', include(admin.site.urls)),

                       (r'^paypal/ipn/', include('paypal.standard.ipn.urls')),
                       (r'^selectable/', include('selectable.urls')),

                       url(r'^mailgun-bounce-notification/$', 'learnscripture.mail.views.mailgun_bounce_notification',
                           name='mailgun-bounce-notification'),
                       )


if settings.DEVBOX:
    urlpatterns = urlpatterns + patterns('',
                                         url(r'^usermedia/(?P<path>.*)$', 'django.views.static.serve',
                                             {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
                                         )


if settings.TESTING:
    urlpatterns += patterns('',
                            url(r'^django_functest/', include('django_functest.urls'))
                            )

urlpatterns = urlpatterns + patterns('',
                                     (r'', 'fiber.views.page'),
                                     )
