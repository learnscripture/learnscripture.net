import os

import django.contrib.staticfiles.views
import django.views.i18n
import django.views.static
import fiber.views
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView

import accounts.lookups
import learnscripture.mail.views
import learnscripture.views

admin.autodiscover()


urlpatterns = [
    # Home page
    url(r'^$', learnscripture.views.home, name='home'),

    # Main views, different for each user
    url(r'^dashboard/$', learnscripture.views.dashboard, name='dashboard'),
    url(r'^choose/$', learnscripture.views.choose, name='choose'),
    url(r'^catechisms/$', learnscripture.views.view_catechism_list, name='catechisms'),
    url(r'^catechisms/(?P<slug>[^/]+)/$', learnscripture.views.view_catechism, name='view_catechism'),
    url(r'^learn-legacy/$', RedirectView.as_view(pattern_name='learn')),
    url(r'^learn/$', learnscripture.views.learn, name='learn'),
    url(r'^preferences/$', learnscripture.views.preferences, name='preferences'),
    url(r'^progress/$', learnscripture.views.user_verses, name='user_verses'),
    url(r'^my-verse-sets/$', learnscripture.views.user_verse_sets, name='user_verse_sets'),
    url(r'^verse-options/$', learnscripture.views.verse_options, name='verse_options'),

    # Payment
    url(r'^donate/$', learnscripture.views.donate, name='donate'),
    url(r'^donation-complete/$', learnscripture.views.pay_done, name='pay_done'),
    url(r'^donation-cancelled/$', learnscripture.views.pay_cancelled, name='pay_cancelled'),

    # Account management
    url(r'^login/$', learnscripture.views.login, name='login'),
    url(r'^signup/$', learnscripture.views.signup, name='signup'),
    url(r'^account/$', learnscripture.views.account_details, name='account_details'),
    url(r'^password-reset/$', learnscripture.views.password_reset_done, name='password_reset_done'),
    url(r'^change-password/$', learnscripture.views.password_change, name='learnscripture_password_change'),
    url(r'^change-password/done/$', learnscripture.views.password_change_done, name='learnscripture_password_change_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$', learnscripture.views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/complete/$', learnscripture.views.password_reset_complete, name='password_reset_complete'),
    url(r'^login/$', learnscripture.views.login, name='admin_password_reset'),
    url(r'^set-language/$', learnscripture.views.set_language, name='learnscripture_set_language'),

    # Verse sets
    url(r'^verse-set/(?P<slug>[^/]+)/$', learnscripture.views.view_verse_set, name='view_verse_set'),
    url(r'^create-selection-set/$', learnscripture.views.create_selection_set, name='create_selection_set'),
    url(r'^create-passage-set/$', learnscripture.views.create_passage_set, name='create_passage_set'),
    url(r'^edit-verse-set/(?P<slug>[^/]+)/$', learnscripture.views.edit_set, name='edit_set'),

    # User stats
    url(r'^user/([^/]*)/$', learnscripture.views.user_stats, name='user_stats'),

    # Activity
    url(r'^activity/$', learnscripture.views.activity_stream, name='activity_stream'),
    url(r'^activity/(\d+)/$', learnscripture.views.activity_item, name='activity_item'),
    url(r'^user/([^/]*)/activity/$', learnscripture.views.user_activity_stream, name='user_activity_stream'),

    # Badges
    url(r'^badges/$', learnscripture.views.awards, name='awards'),
    url(r'^badges/(.*)/$', learnscripture.views.award, name='award'),

    # Groups
    url(r'^groups/$', learnscripture.views.groups, name='groups'),
    url(r'^groups/([^/]*)/$', learnscripture.views.group, name='group'),
    url(r'^groups/([^/]*)/wall/$', learnscripture.views.group_wall, name='group_wall'),
    url(r'^groups/([^/]*)/leaderboard/$', learnscripture.views.group_leaderboard, name='group_leaderboard'),
    url(r'^create-group/$', learnscripture.views.create_group, name='create_group'),
    url(r'^edit-group/(.*)/$', learnscripture.views.edit_group, name='edit_group'),
    url(r'^group-select-list/$', learnscripture.views.group_select_list, name='group_select_list'),
    url(r'^account-autocomplete/$', accounts.lookups.AccountAutocomplete.as_view(), name='account_autocomplete'),

    # Other
    url(r'^contact/$', learnscripture.views.contact, name='contact'),
    url(r'^terms-of-service/$', learnscripture.views.terms_of_service, name='terms_of_service'),
    url(r'^referral-program/$', learnscripture.views.referral_program, name='referral_program'),


    url(r'^stats/$', learnscripture.views.stats, name='stats'),
    url(r'^celery-debug/$', learnscripture.views.celery_debug, name='celery_debug'),
    url(r'^debug/$', learnscripture.views.debug, name='user_debug'),

    # JSON/AJAX views
    url(r'^api/learnscripture/v1/', include('learnscripture.api.urls')),

    # Dependencies
    url(r'^api/v2/', include('fiber.rest_api.urls')),
    url(r'^admin/fiber/', include('fiber.admin_urls')),
    url(r'^jsi18n/$', django.views.i18n.javascript_catalog, {'packages': ['fiber']}),
    url(r'^admin/', admin.site.urls),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    url(r'^paypal/ipn/', include('paypal.standard.ipn.urls')),

    url(r'^mailgun-bounce-notification/$', learnscripture.mail.views.mailgun_bounce_notification,
        name='mailgun-bounce-notification'),

    # Errors

    url(r'^offline/$', learnscripture.views.offline, name='offline'),
    # Also 404.html template and CSRF_FAILURE_VIEW
]


if settings.DEVBOX:
    urlpatterns += [
        url(r'^test-404/(?P<message>.*)$', learnscripture.views.missing)
    ]

if settings.DEVBOX:
    urlpatterns += [
        url(r'^usermedia/(?P<path>.*)$', django.views.static.serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    ]
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns


if settings.TESTING:
    urlpatterns += [
        url(r'^django_functest/', include('django_functest.urls'))
    ]


if settings.DEVBOX:
    # Static files - these are handled by nginx in production, need to add there
    # as well.
    urlpatterns += [
        url(r'^robots\.txt/?$', RedirectView.as_view(url='/static/robots.txt')),
        url(r'^favicon\.ico/?$', RedirectView.as_view(url='/static/img/favicon.png')),
        url(r'^manifest\.webmanifest/?$', RedirectView.as_view(url='/static/manifest.webmanifest')),
        # Browsers refuse to handle service-worker.js if it is returned via a
        # redirect, need to serve directly:
        url(r'^service-worker.js$', lambda request: django.contrib.staticfiles.views.serve(request, 'js/service-worker.js')),
    ]


# Finally, fallback to fiber views
urlpatterns += [
    url('', fiber.views.page),
]

if os.environ.get('TEST_TRACEBACK_PAGES', '') == 'TRUE':
    handler500 = 'learnscripture.tests.base.show_server_error'
