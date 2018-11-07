
### Events:

# Notice in news items when a new verse set is created
# $username is a username (displayed as a link)
# $verseset is the name of the verse set (displayed as a link).
events-verse-set-created-html = { $username } created new verse set { $verseset }

# Notice in news items when a user starts learning a set of verses.
# $username is a username (displayed as a link)
# $verseset is the name of the verse set (displayed as a link).
events-started-learning-verse-set-html = { $username } started learning { $verseset }

# Notice in news items when a user starts to learn a catechism
# $username is a username (displayed as a link)
# $catechism is the name of the catechism (displayed as a link).
events-started-learning-catechism-html = { $username } started learning { $catechism }

# Notice in news items when a user gets an award
# $username is a user's username
# $award is the short description of an award.
# e.g.
#   peter earned Ace level 1
evemts-award-received-html = { $username } earned { $award }

# Notice in news items when a new user joins
events-new-user-signed-up-html = { $username } signed up to LearnScripture.net

# Notice in news items when a user loses an award
# $username is a user's username
# $award is the short description of an award.
# e.g.
#   peter earned Ace level 1
events-award-lost-html = { $username } lost { $award }

# Notice in news items when a user reaches a points milestone
# e.g. 1,000, 10,000 etc.
# $username is a username (displayed as a link)
# $points is the number of points.
events-points-milestone-reached-html = { $username } reached { $points } points

# Notice in news items when a user crosses a milestone in number of verses started
# $username is a username (displayed as a link)
# $verses is the number of verses. Always more than 1.
events-verses-started-milestone-reached-html = { $username } reached { $verses } verses started

# Notice in news items when a user crosses a milestone in number of verses finished
# $username is a username (displayed as a link)
# $verses is the number of verses. Always more than 1.
events-verses-finished-milestone-reached-html = { $username } reached { $verses } verses finished

# Notice in news items when a user joins a group
events-user-joined-group-html = { $username } joined group { $group }

# Notice in news items when a user creates a group
events-user-created-group-html = { $username } created group { $group }

# Notice in news items when a user comments on an event
events-comment-on-activity-html = { $username } posted a <a href="{ $comment_url }">comment</a> on { $other_user }'s activity

# Notice in news items when a user comments on a group wall
events-comment-on-group-wall-html = { $username } posted a <a href="{ $comment_url }">comment</a> on { $group }'s wall

# Notification sent to a user when someone comments on their event.
# $event is a title of an event.
events-you-have-new-comments-notification-html = You have new comments on <b><a href="{ $event_url }">your event</a></b> "{ $event }"

# Notification sent to a user when someone comments on an event
events-new-comments-notification-html = There are <b><a href="{ $event_url }">new comments</a></b> on the event "{ $event }"

# Used as a friendly "when did this happen" timestamp for something done less than one minute ago
events-time-since-just-now = Just now

# Used as a friendly "when did this happen" timestamp for something done less than one hour ago
events-time-since-minutes = { $minutes ->
    [one]    1 minute ago
   *[other]  { $minutes } minutes ago
 }

# Used as a friendly "when did this happen" timestamp for something done less than one day ago
events-time-since-hours = { $hours ->
    [one]    1 hour ago
   *[other]  { $hours } hours ago
 }

# Used as a friendly "when did this happen" timestamp for something done one day ago or longer
events-time-since-days = { $days ->
    [one]    1 day ago
   *[other]  { $days } days ago
 }

