
### Events:

# Notice in news items when a new verse set is created
# $username is a username (displayed as a link)
# $verseset is the name of the verse set (displayed as a link).
events-verse-set-created-html = { $username } { $verseset } başlıklı yeni bir ayet dizini oluşturdu.

# Notice in news items when a user starts learning a set of verses.
# $username is a username (displayed as a link)
# $verseset is the name of the verse set (displayed as a link).
events-started-learning-verse-set-html = { $username } { $verseset } ayet dizini çalışıyor.

# Notice in news items when a user starts to learn a catechism
# $username is a username (displayed as a link)
# $catechism is the name of the catechism (displayed as a link).
events-started-learning-catechism-html = { $username } { $catechism } ilmihalini çalışıyor.

# Notice in news items when a user gets an award
# $username is a user's username
# $award is the short description of an award.
# e.g.
#   peter earned Ace level 1
evemts-award-received-html = { $username } { $award } ödülünü aldı.

# Notice in news items when a new user joins
events-new-user-signed-up-html = { $username } LearnScripture.net sitesine abone oldu

# Notice in news items when a user loses an award
# $username is a user's username
# $award is the short description of an award.
# e.g.
#   peter lost Ace level 1
events-award-lost-html = { $username } { $award } ödülünü kaybetti.

# Notice in news items when a user reaches a points milestone
# e.g. 1,000, 10,000 etc.
# $username is a username (displayed as a link)
# $points is the number of points.
events-points-milestone-reached-html = { $username } { $points } puan aldı.

# Notice in news items when a user crosses a milestone in number of verses started
# $username is a username (displayed as a link)
# $verses is the number of verses. Always more than 1.
events-verses-started-milestone-reached-html = { $username } { $verses } ayeti calışmakta.

# Notice in news items when a user crosses a milestone in number of verses finished
# $username is a username (displayed as a link)
# $verses is the number of verses. Always more than 1.
events-verses-finished-milestone-reached-html = { $username } { $verses } ayeti çalışıp bitirdi.

# Notice in news items when a user joins a group
events-user-joined-group-html = { $username } { $group } grubuna katıldı.

# Notice in news items when a user creates a group
events-user-created-group-html = { $username } { $group } grubunu oluşturdu.

# Notice in news items when a user comments on an event
events-comment-on-activity-html = { $username } { $other_user } adlı kullanıcının hareketlerine <a href="{ $comment_url }">yorum</a> yaptı.

# Notice in news items when a user comments on a group wall
events-comment-on-group-wall-html = { $username } { $group } grubun duvarına <a href="{ $comment_url }">yorum</a> yazdı.

# Notification sent to a user when someone comments on their event.
# $event is a title of an event.
events-you-have-new-comments-notification-html = "{ $event }" başlıklı <b><a href="{ $event_url }">etkinliğiniz</a></b> hakkında yorum yazıldı.

# Notification sent to a user when someone comments on an event
events-new-comments-notification-html = "{ $event }" başlıklı etkinlik yakkında <b><a href="{ $event_url }">yeni yorum</a></b> var.

# Used as a friendly "when did this happen" timestamp for something done less than one minute ago
events-time-since-just-now = Şimdi

# Used as a friendly "when did this happen" timestamp for something done less than one hour ago
events-time-since-minutes = { $minutes } dakika önce

# Used as a friendly "when did this happen" timestamp for something done less than one day ago
events-time-since-hours = { $hours } saat önce

# Used as a friendly "when did this happen" timestamp for something done one day ago or longer
events-time-since-days = { $days } gün önce
