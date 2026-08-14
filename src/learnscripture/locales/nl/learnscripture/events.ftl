
### Events:

# Notice in news items when a new verse set is created
# $username is a username (displayed as a link)
# $verseset is the name of the verse set (displayed as a link).
events-verse-set-created-html = { $username } heeft een nieuwe verzenserie gemaakt: { $verseset }

# Notice in news items when a user starts learning a set of verses.
# $username is a username (displayed as a link)
# $verseset is the name of the verse set (displayed as a link).
events-started-learning-verse-set-html = { $username } is begonnen met het leren van { $verseset }

# Notice in news items when a user starts to learn a catechism
# $username is a username (displayed as a link)
# $catechism is the name of the catechism (displayed as a link).
events-started-learning-catechism-html = { $username } is begonnen met het leren van { $catechism }

# Notice in news items when a user gets an award
# $username is a user's username
# $award is the short description of an award.
# e.g.
#   peter earned Ace level 1
evemts-award-received-html = { $username } heeft { $award } behaald

# Notice in news items when a new user joins
events-new-user-signed-up-html = { $username } heeft zich aangemeld bij LearnScripture.net

# Notice in news items when a user loses an award
# $username is a user's username
# $award is the short description of an award.
# e.g.
#   peter lost Ace level 1
events-award-lost-html = { $username } is { $award } kwijtgeraakt

# Notice in news items when a user reaches a points milestone
# e.g. 1,000, 10,000 etc.
# $username is a username (displayed as a link)
# $points is the number of points.
events-points-milestone-reached-html = { $username } heeft { $points } punten gehaald

# Notice in news items when a user crosses a milestone in number of verses started
# $username is a username (displayed as a link)
# $verses is the number of verses. Always more than 1.
events-verses-started-milestone-reached-html = { $username } is begonnen aan het leren van { $verses } verzen

# Notice in news items when a user crosses a milestone in number of verses finished
# $username is a username (displayed as a link)
# $verses is the number of verses. Always more than 1.
events-verses-finished-milestone-reached-html = { $username } heeft het leren van { $verses } verzen afgerond

# Notice in news items when a user joins a group
events-user-joined-group-html = { $username } is lid geworden van de groep { $group }

# Notice in news items when a user creates a group
events-user-created-group-html = { $username } heeft de groep { $group } aangemaakt

# Notice in news items when a user comments on an event
events-comment-on-activity-html = { $username } liet een a <a href="{ $comment_url }">reactie</a> achter op de activiteit van { $other_user }

# Notice in news items when a user comments on their own event
events-comment-on-own-activity-html = { $username } heeft een <a href="{ $comment_url }">reactie</a> achtergelaten op een eigen activiteit

# Notice in news items when a user comments on a group wall
events-comment-on-group-wall-html = { $username } heeft een <a href="{ $comment_url }">reactie</a> achtergelaten op de muur van { $group }

# Notification sent to a user when someone comments on their event.
# $event is a title of an event.
events-you-have-new-comments-notification-html = Er zijn nieuwe reacties op de <b><a href="{ $event_url }">gebeurtenis</a></b> "{ $event }"

# Notification sent to a user when someone comments on an event
events-new-comments-notification-html = Er zijn <b><a href="{ $event_url }">nieuwe reacties</a></b> op de gebeurtenis "{ $event }"

# Used as a friendly "when did this happen" timestamp for something done less than one minute ago
events-time-since-just-now = Zojuist

# Used as a friendly "when did this happen" timestamp for something done less than one hour ago
events-time-since-minutes = { $minutes ->
    [one]    1 minuut geleden
   *[other]  { $minutes } minuten geleden
 }

# Used as a friendly "when did this happen" timestamp for something done less than one day ago
events-time-since-hours = { $hours ->
    [one]    1 uur geleden
   *[other]  { $hours } uur geleden
 }

# Used as a friendly "when did this happen" timestamp for something done one day ago or longer
events-time-since-days = { $days ->
    [one]    1 dag geleden
   *[other]  { $days } dagen geleden
 }
