from django.conf.urls import url

from learnscripture.api import handlers
# These URLs are hardcoded into Javascript instead of using URL reversing
# somehow. That's OK, because if you want to change them, you should be adding
# to them first for the sake of Javascript that is already loaded into the
# browser, and then only remove the old one when you are sure no javascript will
# try to use it.
urlpatterns = [
    url(r'^versestolearn2/$', handlers.VersesToLearnHandler.as_view(), name='learnscripture.api.versestolearn2'),
    url(r'^versestolearn/$', handlers.VersesToLearnHandler.as_view(), name='learnscripture.api.versestolearn'),
    url(r'^actioncomplete/$', handlers.ActionCompleteHandler.as_view(), name='learnscripture.api.actioncomplete'),
    url(r'^logout/$', handlers.LogOutHandler.as_view(), name='learnscripture.api.logout'),
    url(r'^setpreferences/$', handlers.SetPreferences.as_view(), name='learnscripture.api.setpreferences'),
    url(r'^sessionstats/$', handlers.SessionStats.as_view(), name='learnscripture.api.sessionstats'),
    url(r'^skipverse/$', handlers.SkipVerseHandler.as_view(), name='learnscripture.api.skipverse'),
    url(r'^cancellearningverse/$', handlers.CancelLearningVerseHandler.as_view(), name='learnscripture.api.cancellearningverse'),
    url(r'^cancellearningpassage/$', handlers.CancelLearningPassageHandler.as_view(), name='learnscripture.api.cancellearningpassage'),
    url(r'^resetprogress/$', handlers.ResetProgressHandler.as_view(), name='learnscripture.api.resetprogress'),
    url(r'^reviewsooner/$', handlers.ReviewSoonerHandler.as_view(), name='learnscripture.api.reviewsooner'),
    url(r'^actionlogs/$', handlers.ActionLogs.as_view(), name='learnscripture.api.actionlogs'),
    url(r'^versefind/$', handlers.VerseFind.as_view(), name='learnscripture.api.versefind'),
    url(r'^addversetoqueue/$', handlers.AddVerseToQueue.as_view(), name='learnscripture.api.addversetoqueue'),
    url(r'^checkduplicatepassageset/$', handlers.CheckDuplicatePassageSet.as_view(), name='learnscripture.api.checkduplicatepassageset'),
    url(r'^deletenotice/$', handlers.DeleteNotice.as_view(), name='learnscripture.api.deletenotice'),
    url(r'^addcomment/$', handlers.AddComment.as_view(), name='learnscripture.api.addcomment'),
    url(r'^hidecomment/$', handlers.HideComment.as_view(), name='learnscripture.api.hidecomment'),
    url(r'^follow/$', handlers.Follow.as_view(), name='learnscripture.api.follow'),
    url(r'^unfollow/$', handlers.UnFollow.as_view(), name='learnscripture.api.unfollow'),
    url(r'^savemiscpreferences/$', handlers.SaveMiscPreferences.as_view(), name='learnscripture.api.savemiscpreferences'),
]
