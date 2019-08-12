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

awards-the-following-are-available = The following badges are available:


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
awards-you-dont-have-this-award = You don't have this badge yet.

# Message used when trying to view some old awards
awards-removed = The ‘{ $name }’ badge is an old badge that is no longer used

## 'Student' award.

# Name
awards-student-award-name = Student

# General description
awards-student-award-general-description = Awarded for starting to learn verses. Level 1 is for 1 verse, going up to level 9 for the whole Bible.

# Description for a specific level
awards-student-award-level-n-description = Learning at least { $verse_count ->
    [one]    1 verse
   *[other]  { $verse_count } verses
 }

# Specific description for level 9
awards-student-award-level-9-description = Learning the whole bible!

## 'Master' award.

# Name
awards-master-award-name = Master

# General description
awards-master-award-general-description =
   Awarded for fully learning verses (5 stars). This takes about year, to make
   sure verses are really in there for good! Level 1 is for 1 verse, going up to
   level 9 for the whole Bible.

# Description for a specific level
awards-master-award-level-n-description = Finished learning at least { $verse_count ->
    [one]     1 verse
   *[other]   { $verse_count } verses
 }

# Specific description for level 9
awards-master-award-level-9-description = Finished learning the whole bible!

## 'Sharer' award.

# Name
awards-sharer-award-name = Sharer

# General description
awards-sharer-award-general-description =
    Awarded for creating public verse sets (selections).
    Levels go from 1 for 1 verse set, to level 5 for 20 verse sets.

# Description for a specific level
awards-sharer-award-level-n-description = { $count ->
      [one]    Created a public selection verse sets
     *[other]  Created { $count } public selection verse sets
  }


## 'Trend Setter' award.

# Name
awards-trend-setter-award-name = Trend setter

# General description
awards-trend-setter-award-level-general-description =
    Awarded for creating verse sets that other people actually use.
    Level 1 is given when 5 other people are using one of your verse sets.

# Description for a specific level
awards-trend-setter-award-level-n-description = Verse sets created by this user have been used by others at least { $count } times.


## 'Ace' award.

# Name
awards-ace-award-name = Ace

# General description
awards-ace-award-general-description = Awarded for getting 100% in a test. Level 1 is for getting it once, level 2 if you do it twice in a row, level 3 for 4 times in a row, level 4 for 8 times in a row etc.

# Description for first level
awards-ace-award-level-1-description = Achieved 100% in a test

# Description for a specific level.
# $count is the number of times in a row they got 100%,
# will always be greater than 1.
awards-ace-award-level-n-description = Achieved 100%% in a test { $count } times in a row


## 'Recruiter' award.

# Name
awards-recruiter-award-name = Recruiter

# General description
# $url is a URL for the referral program help page.
awards-recruiter-award-general-description-html =
   Awarded for getting other people to sign up using our <a href="{ $url }">referral program</a>. Level 1 is for one referral, and is worth 20,000 points.

# Description for a specific level 'Recruiter' award.
# $url is a URL for the referral program help page.
# $count is the number of people recruited.
awards-recruiter-award-level-n-description-html = { $count ->
     [one]   Got 1 person to sign up to LearnScripture.net through our <a href='{ $url }'>referral program</a>
    *[other] Got { $count } people to sign up to LearnScripture.net through our <a href='{ $url }'>referral program</a>
 }

## 'Addict' award.

# Name
awards-addict-award-name = Addict

# General description for 'Addict' award
awards-addict-award-general-description = Awarded to users who've done verse tests during every hour on the clock.

# Description for 'Addict' award that appears on awardee's page
awards-addict-award-level-all-description = Done verse tests during every hour on the clock


## 'Organizer' award.

# Name
awards-organizer-award-name = Organizer

# General description
awards-organizer-award-general-description = Awarded for getting people to together in groups. First level requires 5 people to join one of your groups.

# Description for a specific level
awards-organizer-award-level-n-description = Created groups that are used by at least { $count } people

## 'Consistent learner' award.

# Name
awards-consistent-learner-award-name = Consistent learner

# General description
awards-consistent-learner-award-general-description = Awarded for starting to learn a new verse every day without gaps, over a period of time. Note that you have to keep learning the verses for them to be counted. Days are defined by the UTC time zone. Level 1 is for 1 week, level 9 is for 2 years.

# Specific description for level 1
awards-consistent-learner-award-level-1-description = Started learning a new verse every day for 1 week
awards-consistent-learner-award-level-2-description = Started learning a new verse every day for 2 weeks
awards-consistent-learner-award-level-3-description = Started learning a new verse every day for 1 month
awards-consistent-learner-award-level-4-description = Started learning a new verse every day for 3 months
awards-consistent-learner-award-level-5-description = Started learning a new verse every day for 6 months
awards-consistent-learner-award-level-6-description = Started learning a new verse every day for 9 months
awards-consistent-learner-award-level-7-description = Started learning a new verse every day for 1 year
awards-consistent-learner-award-level-8-description = Started learning a new verse every day for 18 months
awards-consistent-learner-award-level-9-description = Started learning a new verse every day for 2 years

# Title for award at a specific level.
# $name is award name,
# $level is a number indicating level.
awards-level-title = { $name } - level { $level }

# Caption indicating a specific level award for a specific user
awards-level-awarded-for-user = { $award_name } level { $award_level } award for { $username }
