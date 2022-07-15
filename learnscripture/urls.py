import os

import django.contrib.staticfiles.views
import django.views.i18n
import django.views.static
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView

import accounts.lookups
import cms.views
import learnscripture.views

admin.autodiscover()


urlpatterns = [
    # Home page
    path("", learnscripture.views.home, name="home"),
    # Main views, different for each user
    path("dashboard/", learnscripture.views.dashboard, name="dashboard"),
    path("choose/", learnscripture.views.choose, name="choose"),
    path("choose-set/", learnscripture.views.handle_choose_set, name="handle_choose_set"),
    path("choose-verse/", learnscripture.views.handle_choose_verse, name="handle_choose_verse"),
    path("catechisms/", learnscripture.views.view_catechism_list, name="catechisms"),
    path("catechisms/<slug:slug>/", learnscripture.views.view_catechism, name="view_catechism"),
    path("learn-legacy/", RedirectView.as_view(pattern_name="learn")),
    path("learn/", learnscripture.views.learn, name="learn"),
    path("preferences/", learnscripture.views.preferences, name="preferences"),
    path("progress/", learnscripture.views.user_verses, name="user_verses"),
    path("my-verse-sets/", learnscripture.views.user_verse_sets, name="user_verse_sets"),
    path("verse-options/", learnscripture.views.verse_options, name="verse_options"),
    # Payment
    path("donate/", learnscripture.views.donate, name="donate"),
    path("donation-complete/", learnscripture.views.pay_done, name="pay_done"),
    path("donation-cancelled/", learnscripture.views.pay_cancelled, name="pay_cancelled"),
    # Account management
    path("login/", learnscripture.views.login, name="login"),
    path("signup/", learnscripture.views.signup, name="signup"),
    path("account/", learnscripture.views.account_details, name="account_details"),
    path("password-reset/", learnscripture.views.password_reset_done, name="password_reset_done"),
    path("change-password/", learnscripture.views.password_change, name="learnscripture_password_change"),
    path(
        "change-password/done/", learnscripture.views.password_change_done, name="learnscripture_password_change_done"
    ),
    path("reset/<str:uidb64>/<str:token>/", learnscripture.views.password_reset_confirm, name="password_reset_confirm"),
    path("reset/complete/", learnscripture.views.password_reset_complete, name="password_reset_complete"),
    path("login/", learnscripture.views.login, name="admin_password_reset"),
    path("set-language/", learnscripture.views.set_language, name="learnscripture_set_language"),
    # Verse sets
    path("verse-set/<slug:slug>/", learnscripture.views.view_verse_set, name="view_verse_set"),
    path("create-selection-set/", learnscripture.views.create_selection_set, name="create_selection_set"),
    path("create-passage-set/", learnscripture.views.create_passage_set, name="create_passage_set"),
    path("edit-verse-set/<slug:slug>/", learnscripture.views.edit_set, name="edit_set"),
    # User stats
    path("user/<str:username>/", learnscripture.views.user_stats, name="user_stats"),
    # Activity
    path("activity/", learnscripture.views.activity_stream, name="activity_stream"),
    path("activity/<int:event_id>/", learnscripture.views.activity_item, name="activity_item"),
    path("user/<str:username>/activity/", learnscripture.views.user_activity_stream, name="user_activity_stream"),
    # Badges
    path("badges/", learnscripture.views.awards, name="awards"),
    path("badges/<slug:slug>/", learnscripture.views.award, name="award"),
    # Groups
    path("groups/", learnscripture.views.groups, name="groups"),
    path(
        "groups/<slug:slug>/",
        include(
            [
                path("", learnscripture.views.group, name="group"),
                path("wall/", learnscripture.views.group_wall, name="group_wall"),
                path("leaderboard/", learnscripture.views.group_leaderboard, name="group_leaderboard"),
            ]
        ),
    ),
    path("create-group/", learnscripture.views.create_group, name="create_group"),
    path("edit-group/<slug:slug>/", learnscripture.views.edit_group, name="edit_group"),
    path("group-select-list/", learnscripture.views.group_select_list, name="group_select_list"),
    path("account-autocomplete/", accounts.lookups.AccountAutocomplete.as_view(), name="account_autocomplete"),
    # CMS
    path("api/cms/", include("cms.rest_api.urls")),
    # Other
    path("contact/", learnscripture.views.contact, name="contact"),
    path("terms-of-service/", learnscripture.views.terms_of_service, name="terms_of_service"),
    path("referral-program/", learnscripture.views.referral_program, name="referral_program"),
    path("stats/", learnscripture.views.stats, name="stats"),
    path("task-queue-debug/", learnscripture.views.task_queue_debug, name="task_queue_debug"),
    path("debug/", learnscripture.views.debug, name="user_debug"),
    # JSON/AJAX views
    path("api/learnscripture/v1/", include("learnscripture.api.urls")),
    # Dependencies
    path("admin/cms/", include("cms.admin_urls")),
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("paypal/ipn/", include("paypal.standard.ipn.urls")),
    # Errors
    path("offline/", learnscripture.views.offline, name="offline"),
    # Also 404.html template and CSRF_FAILURE_VIEW
]


if settings.DEVBOX:
    urlpatterns += [
        path("test-404/<str:message>", learnscripture.views.missing),
        path("test-500/", learnscripture.views.test_500),
        path("test-500-real/", learnscripture.views.test_500_real),
    ]

if settings.DEVBOX:
    urlpatterns += [
        path(
            "usermedia/<path:path>",
            django.views.static.serve,
            {"document_root": settings.MEDIA_ROOT, "show_indexes": True},
        ),
    ]
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns


if settings.TESTS_RUNNING:
    urlpatterns += [path("django_functest/", include("django_functest.urls"))]


if settings.DEVBOX:
    # Static files - these are handled by nginx in production, need to add there
    # as well.
    urlpatterns += [
        path("robots.txt", RedirectView.as_view(url="/static/robots.txt")),
        path("favicon.ico", RedirectView.as_view(url="/static/img/favicon.png")),
        path("manifest.webmanifest", RedirectView.as_view(url="/static/manifest.webmanifest")),
        # Browsers refuse to handle service-worker.js if it is returned via a
        # redirect, need to serve directly:
        path(
            "service-worker.js", lambda request: django.contrib.staticfiles.views.serve(request, "js/service-worker.js")
        ),
    ]


# Finally, fallback to cms views
urlpatterns += [
    re_path("", cms.views.cms_page),
]

if os.environ.get("TEST_TRACEBACK_PAGES", "") == "TRUE":
    handler500 = "learnscripture.tests.base.show_server_error"
else:
    handler500 = learnscripture.views.handler500
