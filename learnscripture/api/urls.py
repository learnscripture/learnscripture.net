from django.urls import path

from learnscripture.api import handlers

# These URLs are hardcoded into Javascript instead of using URL reversing
# somehow. That's OK, because if you want to change them, you should be adding
# to them first for the sake of Javascript that is already loaded into the
# browser, and then only remove the old one when you are sure no javascript will
# try to use it.
urlpatterns = [
    path("versestolearn2/", handlers.VersesToLearnHandler.as_view(), name="learnscripture.api.versestolearn2"),
    path("versestolearn/", handlers.VersesToLearnHandler.as_view(), name="learnscripture.api.versestolearn"),
    path("actioncomplete/", handlers.ActionCompleteHandler.as_view(), name="learnscripture.api.actioncomplete"),
    path("setpreferences/", handlers.SetPreferences.as_view(), name="learnscripture.api.setpreferences"),
    path("sessionstats/", handlers.SessionStats.as_view(), name="learnscripture.api.sessionstats"),
    path("skipverse/", handlers.SkipVerseHandler.as_view(), name="learnscripture.api.skipverse"),
    path(
        "cancellearningverse/",
        handlers.CancelLearningVerseHandler.as_view(),
        name="learnscripture.api.cancellearningverse",
    ),
    path(
        "cancellearningpassage/",
        handlers.CancelLearningPassageHandler.as_view(),
        name="learnscripture.api.cancellearningpassage",
    ),
    path("resetprogress/", handlers.ResetProgressHandler.as_view(), name="learnscripture.api.resetprogress"),
    path("reviewsooner/", handlers.ReviewSoonerHandler.as_view(), name="learnscripture.api.reviewsooner"),
    path("actionlogs/", handlers.ActionLogs.as_view(), name="learnscripture.api.actionlogs"),
    path("versefind/", handlers.VerseFind.as_view(), name="learnscripture.api.versefind"),
    path("deletenotice/", handlers.DeleteNotice.as_view(), name="learnscripture.api.deletenotice"),
    path("addcomment/", handlers.AddComment.as_view(), name="learnscripture.api.addcomment"),
    path("savemiscpreferences/", handlers.SaveMiscPreferences.as_view(), name="learnscripture.api.savemiscpreferences"),
    path("usertimelinestats/", handlers.UserTimelineStats.as_view(), name="learnscripture.api.usertimelinestats"),
]
