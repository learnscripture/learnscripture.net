
### Events:

# Notice in news items when a new verse set is created
# $username is a username (displayed as a link)
# $verseset is the name of the verse set (displayed as a link).
events-verse-set-created-html = { $username } creó un nuevo conjunto de versículos { $verseset }

# Notice in news items when a user starts learning a set of verses.
# $username is a username (displayed as a link)
# $verseset is the name of the verse set (displayed as a link).
events-started-learning-verse-set-html = { $username } comenzó a memorizar { $verseset }

# Notice in news items when a user starts to learn a catechism
# $username is a username (displayed as a link)
# $catechism is the name of the catechism (displayed as a link).
events-started-learning-catechism-html = { $username } comenzó a memorizar { $catechism }

# Notice in news items when a user gets an award
# $username is a user's username
# $award is the short description of an award.
# e.g.
#   peter earned Ace level 1
evemts-award-received-html = { $username } obtuvo { $award }

# Notice in news items when a new user joins
events-new-user-signed-up-html = { $username } se unió a LearnScripture.net

# Notice in news items when a user loses an award
# $username is a user's username
# $award is the short description of an award.
# e.g.
#   peter lost Ace level 1
events-award-lost-html = { $username } perdió { $award }

# Notice in news items when a user reaches a points milestone
# e.g. 1,000, 10,000 etc.
# $username is a username (displayed as a link)
# $points is the number of points.
events-points-milestone-reached-html = { $username } alcanzó { $points } puntos

# Notice in news items when a user crosses a milestone in number of verses started
# $username is a username (displayed as a link)
# $verses is the number of verses. Always more than 1.
events-verses-started-milestone-reached-html = { $username } alcanzó { $verses } versículos comenzados

# Notice in news items when a user crosses a milestone in number of verses finished
# $username is a username (displayed as a link)
# $verses is the number of verses. Always more than 1.
events-verses-finished-milestone-reached-html = { $username } alcanzó { $verses } versículos terminados

# Notice in news items when a user joins a group
events-user-joined-group-html = { $username } se unió al grupo { $group }

# Notice in news items when a user creates a group
events-user-created-group-html = { $username } creó el grupo { $group }

# Notice in news items when a user comments on an event
events-comment-on-activity-html = { $username } publicó un <a href="{ $comment_url }">comentario</a> en la actividad de { $other_user }

# Notice in news items when a user comments on their own event
events-comment-on-own-activity-html = { $username } publicó un <a href="{ $comment_url }">comentario</a> en su actividad

# Notice in news items when a user comments on a group wall
events-comment-on-group-wall-html = { $username } publicó un <a href="{ $comment_url }">comentario</a> en el muro de { $group }

# Notification sent to a user when someone comments on their event.
# $event is a title of an event.
events-you-have-new-comments-notification-html = Tienes nuevos comentarios en <b><a href="{ $event_url }">tu evento</a></b> "{ $event }"

# Notification sent to a user when someone comments on an event
events-new-comments-notification-html = Hay <b><a href="{ $event_url }">nuevos comentarios</a></b> en el evento "{ $event }"

# Used as a friendly "when did this happen" timestamp for something done less than one minute ago
events-time-since-just-now = Justo ahora

# Used as a friendly "when did this happen" timestamp for something done less than one hour ago
events-time-since-minutes = hace { $minutes ->
    [one]    un minuto
   *[other]  { $minutes } minutos
 }

# Used as a friendly "when did this happen" timestamp for something done less than one day ago
events-time-since-hours = hace { $hours ->
    [one]    una hora
   *[other]  { $hours } horas
 }

# Used as a friendly "when did this happen" timestamp for something done one day ago or longer
events-time-since-days = hace { $days ->
    [one]    un día
   *[other]  { $days } días
 }
