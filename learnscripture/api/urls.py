from django.conf.urls import url, patterns

from learnscripture.api.handlers import VersesToLearnHandler, ActionCompleteHandler, ChangeVersionHandler, LogOutHandler, SetPreferences, SessionStats, SkipVerseHandler, CancelLearningVerseHandler, CancelLearningPassageHandler, ScoreLogs, VerseFind, CheckDuplicatePassageSet, DeleteNotice, ResetProgressHandler, AndroidAppInstalled, AddComment, HideComment, Follow, UnFollow, RecordWordMistakes


# These URLs are hardcoded into Javascript instead of using URL reversing
# somehow. That's OK, because if you want to change them, you should be adding
# to them first for the sake of Javascript that is already loaded into the
# browser, and then only remove the old one when you are sure no javascript will
# try to use it.
urlpatterns = patterns('',
                       url(r'^versestolearn/$', VersesToLearnHandler.as_view(), name='learnscripture.api.versestolearn'),
                       url(r'^actioncomplete/$', ActionCompleteHandler.as_view(), name='learnscripture.api.actioncomplete'),
                       url(r'^recordwordmistakes/$', RecordWordMistakes.as_view(), name='learnscripture.api.recordwordmistakes'),
                       url(r'^changeversion/$', ChangeVersionHandler.as_view(), name='learnscripture.api.changeversion'),
                       url(r'^logout/$', LogOutHandler.as_view(), name='learnscripture.api.logout'),
                       url(r'^setpreferences/$', SetPreferences.as_view(), name='learnscripture.api.setpreferences'),
                       url(r'^sessionstats/$', SessionStats.as_view(), name='learnscripture.api.sessionstats'),
                       url(r'^skipverse/$', SkipVerseHandler.as_view(), name='learnscripture.api.skipverse'),
                       url(r'^cancellearningverse/$', CancelLearningVerseHandler.as_view(), name='learnscripture.api.cancellearningverse'),
                       url(r'^cancellearningpassage/$', CancelLearningPassageHandler.as_view(), name='learnscripture.api.cancellearningpassage'),
                       url(r'^resetprogress/$', ResetProgressHandler.as_view(), name='learnscripture.api.resetprogress'),
                       url(r'^scorelogs/$', ScoreLogs.as_view(), name='learnscripture.api.scorelogs'),
                       url(r'^versefind/$', VerseFind.as_view(), name='learnscripture.api.versefind'),
                       url(r'^checkduplicatepassageset/$', CheckDuplicatePassageSet.as_view(), name='learnscripture.api.checkduplicatepassageset'),
                       url(r'^deletenotice/$', DeleteNotice.as_view(), name='learnscripture.api.deletenotice'),
                       url(r'^androidappinstalled/$', AndroidAppInstalled.as_view(), name='learnscripture.api.androidappinstalled'),
                       url(r'^addcomment/$', AddComment.as_view(), name='learnscripture.api.androidappinstalled'),
                       url(r'^hidecomment/$', HideComment.as_view(), name='learnscripture.api.hidecomment'),
                       url(r'^follow/$', Follow.as_view(), name='learnscripture.api.follow'),
                       url(r'^unfollow/$', UnFollow.as_view(), name='learnscripture.api.unfollow'),
                       )
