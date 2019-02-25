## Awards/badges.

# Notification received when a user gets a new award/badge,
# $award is the award name (appears as a link)
awards-new-award-html = You've earned a new badge: { $award }.

# Notification received when a user gets a higher level for an award/badge
# $award is the award name (appears as a link)
awards-levelled-up-html = You've levelled up on one of your badges: { $award }.

# Notification when there are points for an award that has been received.
# $points is the number of points given
awards-points-bonus =  Points bonus: { $points }.

# Appears next to notification about new award, as shortcuts for
# telling other people about the award.
# $twitter is a link to Twitter.
# $facebook is a link to Facebook.
awards-tell-people-html = Tell people: { $facebook } { $twitter }

# Default message that is used for sharing about awards on twitter/facebook
# $award is the award name/description
awards-social-media-default-message = I just earned a badge: { $award }

## Awards page.

# Page title
awards-page-title = Badges

awards-the-following-are-available = The following badges are available.


# Caption in table header for award name/icon
awards-award = Badge

# Caption in table header for when the award was received
awards-date-received = Date

# Caption in table header for award icon
awards-icon = Icon

# Caption in table header for award description
awards-description = Description

# Caption in the table header for award points
awards-points = Points

# Indicates the level of an award/badge
awards-award-level = level { $level }

# Indicates the highest level that has so been achieved for the award
award-highest-level-achieved-html = Highest level achieved so far: <b>Level { $level }</b>

# Link to page showing details about who has achieved the award,
# $name is the name/short description of the award
award-people-with-award = People with { $name } badge



## Individual award page.

# Page title,
# $name is the award name/short description
awards-award-page-title = Badge - { $name }

# Heading for description of award
awards-description-subtitle = Description

# Heading for list of people who have achieved the award
awards-achievers-subtitle = Achievers

# Indicates the highest level that can be achieved for an award
awards-award-highest-level = Level { $level } is the highest level.

# Subtitle
awards-level-subtitle = Level { $level }

# Indicates the number of people who have achieved the award at this level, followed
# by a list containing all those users
awards-level-achievers-all = Total { $count ->
    [one]    1 user
   *[other]  { $count } users
 }:

# Indicates the number of people who have achieved the award at this level, followed
# by a list containing a sample of those users.
awards-level-achievers-truncated = Total { $count ->
    [one]    1 user
   *[other]  { $count } users
 }, including:


# Link to page showing all badges
awards-all-available-badges = All available badges

# Link to page showing user's badges
awards-your-badges = Your badges

# Subtitle for section describing the user's level for the award being described
awards-your-level = Your level

# Used when the award has levels, and the user has the award at a certain level
awards-you-have-this-award-at-level = You have this badge, at level { $level }.

# Used when the award has does not have levels, and the user has the award.
awards-you-have-this-award = You have this badge.

# Used when the user doesn't have the award
awards-you-dont-have-this-badge = You don't have this badge yet.

# Message used when trying to view some old awards
awards-removed = The ‘{ $name }’ badge is an old badge that is no longer used
