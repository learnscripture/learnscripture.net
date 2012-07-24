from django.conf.urls import patterns, include, url
from django.conf import settings
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
                       url(r'^learn/$', 'learnscripture.views.learn', name='learn'),
                       url(r'^preferences/$', 'learnscripture.views.preferences', name='preferences'),
                       url(r'^progress/$', 'learnscripture.views.user_verses', name='user_verses'),
                       url(r'^my-verse-sets/$', 'learnscripture.views.user_verse_sets', name='user_verse_sets'),

                       # Payment
                       url(r'^subscribe/$', 'learnscripture.views.subscribe', name='subscribe'),
                       url(r'^payment-complete/$', 'learnscripture.views.pay_done', name='pay_done'),
                       url(r'^payment-cancelled/$', 'learnscripture.views.pay_cancelled', name='pay_cancelled'),

                       # Account management
                       url(r'^login/$', 'learnscripture.views.login', name='login'),
                       url(r'^account/$', 'learnscripture.views.account_details', name='account_details'),
                       url(r'^password-reset/$', 'learnscripture.views.password_reset_done', name='password_reset_done'),
                       url(r'^reset/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', 'learnscripture.views.password_reset_confirm', name='password_reset_confirm'),
                       url(r'^reset/complete/$', 'learnscripture.views.password_reset_complete', name='password_reset_complete'),

                       # Payment funds
                       url(r'^payment-funds/$', 'learnscripture.views.account_funds', name='account_funds'),
                       url(r'^payment-funds/new/$', 'learnscripture.views.add_account_fund', name='add_account_fund'),
                       url(r'^payment-funds/(\d+)/$', 'learnscripture.views.edit_account_fund', name='edit_account_fund'),
                       url(r'^topup-fund/(\d+)/$', 'learnscripture.views.topup_fund', name='topup_fund'),
                       url(r'^fund-payment-complete/$', 'learnscripture.views.fund_pay_done', name='fund_pay_done'),
                       url(r'^fund-payment-cancelled/$', 'learnscripture.views.fund_pay_cancelled', name='fund_pay_cancelled'),

                       # Verse sets
                       url(r'^verse-set/(?P<slug>[^/]+)/$', 'learnscripture.views.view_verse_set', name='view_verse_set'),
                       url(r'^create-verse-set/$', 'learnscripture.views.create_set_menu', name='create_set_menu'),
                       url(r'^create-selection-set/$', 'learnscripture.views.create_selection_set', name='create_selection_set'),
                       url(r'^create-passage-set/$', 'learnscripture.views.create_passage_set', name='create_passage_set'),
                       url(r'^edit-verse-set/(?P<slug>[^/]+)/$', 'learnscripture.views.edit_set', name='edit_set'),

                       # User stats
                       url(r'^leaderboard/$', 'learnscripture.views.leaderboard', name='leaderboard'),
                       url(r'^user/(.*)/$', 'learnscripture.views.user_stats', name='user_stats'),

                       # Badges
                       url(r'^badges/$', 'learnscripture.views.awards', name='awards'),
                       url(r'^badges/(.*)/$', 'learnscripture.views.award', name='award'),

                       # Groups
                       url(r'^groups/$', 'learnscripture.views.groups', name='groups'),
                       url(r'^groups/(.*)/$', 'learnscripture.views.group', name='group'),
                       url(r'^create-group/$', 'learnscripture.views.create_group', name='create_group'),
                       url(r'^edit-group/(.*)/$', 'learnscripture.views.edit_group', name='edit_group'),
                       url(r'^group-select-list/$', 'learnscripture.views.group_select_list', name='group_select_list'),

                       # Other
                       url(r'^contact/$', 'learnscripture.views.contact', name='contact'),
                       url(r'^terms-of-service/$', 'learnscripture.views.terms_of_service', name='terms_of_service'),
                       url(r'^referral-program/$', 'learnscripture.views.referral_program', name='referral_program'),


                       url(r'^stats/$', 'learnscripture.views.stats', name='stats'),

                       # JSON/AJAX views
                       (r'^api/learnscripture/v1/', include('learnscripture.api.urls')),

                       # Dependencies
                       (r'^admin/fiber/', include('fiber.admin_urls')),
                       (r'^api/v1/', include('fiber.api.urls')),
                       (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('fiber',),}),
                       url(r'^admin/', include(admin.site.urls)),

                       (r'^paypal/ipn/', include('paypal.standard.ipn.urls')),
                       (r'^selectable/', include('selectable.urls')),

                       (r'', 'fiber.views.page'),
)


if settings.DEBUG:
    urlpatterns = urlpatterns + patterns('',
                           url(r'^usermedia/(?P<path>.*)$', 'django.views.static.serve',
                               {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
                           )
