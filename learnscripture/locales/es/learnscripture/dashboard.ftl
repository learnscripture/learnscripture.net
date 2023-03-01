### Dashboard page
# Title of 'dashboard' page
dashboard-page-title = Dashboard

# Notice that appears for guest users who haven't created an account yet
dashboard-remember-to-create-an-account-html =
    <b>Remember to <a href="{ $signup_url }">create an account</a></b> -
    otherwise your progress will be lost! It's free, only takes a few seconds, and
    enables lots of additional features like badges, groups, leaderboards and
    statistics pages. As a guest, your data will expire on { DATETIME($expires) }.


## Unfinished session section.

# Sub title
dashboard-continue-title =
    Continue

dashboard-unfinished-notice = You have an unfinished session.

dashboard-unfinished-notice-part-2 = Continue the session to sync unsaved data.

# Caption for button that will continue the session
dashboard-continue-button = Continue

## Heatmap section.

dashboard-learning-events = Learning events

## Review section.

# Sub title
dashboard-review-title = Review

# Button for reviewing a whole passage
dashboard-review-whole-passage-button = Whole passage

# Button for reviewing one section of a passage.
# $verse_count is the number of verses in that section.
dashboard-review-one-section-button = One section ({ $verse_count } vss)

# Button for reviewing a verse or set of verses, or a catechism question
dashboard-review-button = Review

# Button for cancelling learning a verse/passage
dashboard-cancel-learning = Cancel

# Note shown when the whole passage is due for review
# $verse_count is the number of verses in the passage
dashboard-passage-due-for-review = This passage is due for review ({ $verse_count } verses).

# Note shown when part of a passage verse set is due for review.
# $needs_testing_count is the number that are due for review,
# $total_verse_count is the total number of verses in the passage
dashboard-passage-part-due-for-review = Part of this passage is due for review ({ $needs_testing_count }/{ $total_verse_count } verses).

# Indicates the number of verses due for review (separate from the passage verse sets)
dashboard-verses-for-review-count = You've currently got
  { $count ->
    [one]     1 verse
   *[other]  { $count } verses
  } due for review.

# Displayed before a list of verse references that are due for review or learning
dashboard-verses-coming-up = Verses coming up:

# Indicates the number of catechism questions due for review
dashboard-catechism-questions-for-review-count = You've currently got { $count } question(s) due for review.

# Message shown if there is nothing in the general queue due for reviewing. (Excludes passage verse sets)
dashboard-general-queue-empty = Nothing in your general queue needs reviewing at this point in time.

# Message about the next verse due for review.
# $title is the verse reference or catechism title,
# $timeuntil is a string like "5 minutes" or "3 hours"
dashboard-next-item-due-html = Next item due for review: <b>{ $title }</b> in { $timeuntil }


## Learn section.

# Sub title
dashboard-learn-title = Learn

# Button to start learning a passage
dashboard-learn-start-learning-button = Start learning

# Button to continue learning a passage (they have already started at least one verse)
dashboard-learn-continue-learning-button = Continue learning

# Message displayed for a passage set that is in the user's queue
# for learning (but that haven't started yet)
dashboard-passage-queued = You've queued this passage for learning.

# Message on a passage verse set indicating the number of items learned
# and still not started.
dashboard-passages-youve-seen-verses =
    You've seen { $tested_total ->
            [1]     1 verse
           *[other] { $tested_total } verses
     } so far,
     with { $untested_total } still to start on.

# Message on a passage verse set indicating the number of items learned
# and still not started, inluding info about those that are due for review.
dashboard-passages-youve-seen-verses-with-review-due-html =
    You've seen { $tested_total ->
            [1]     1 verse
           *[other] { $tested_total } verses
     } so far,
    <b>{ $needs_review_total } due for review</b>,
    with { $untested_total } still to start on.


# Sub title for verses that aren't part of a verse set
dashboard-learn-other-verses = Other verses

# Shows number of verses in queue for learning
dashboard-queued-verses = You've queued { $count } new verses for learning.

# Shows number of verses in a particular set in queue for learning
dashboard-queued-verses-in-set = You've queued { $count } new verses for learning in this set.

# Button to learn a verse or queue of verses
dashboard-learn-button = Learn

# Button to remove items from the queue of verses to learn
dashboard-clear-queue-button = Clear

# Indicates the total number of questions in a catechism that has been queued for learning
dashboard-catechism-question-count = You've queued this catechism for learning, { $count } questions total.

# Indicates the number of questions in a catechism that have been started, and how many remain.
dashboard-catechism-learned-and-remanining-count = You've seen
   { $started_count ->
       [one]     1 question
      *[other]   { $started_count } questions
   } so far,
   with { $remaining_count } to go.

# Message displayed when there are no passages, verses or catechisms queued for learning
dashboard-learn-nothing-in-queue = Nothing currently in your queue for learning.

# Confirmation prompt after clicking 'clear queue' button for verses
dashboard-remove-verses-from-queue-confirm = This will remove chosen verses from your queue for learning. To learn them you will have to select the verses or verse sets again. Continue?

# Confirmation prompt after clicking 'cancel' button for a catechism
dashboard-remove-catechism-from-queue = This will remove chosen catechism questions from your queue for learning. To learn them you will have to "select the catechism again. Continue?

# Confirmation prompt after clicking 'cancel' for a passage verse set
dashboard-cancel-passage-confirm = This will cancel learning this passage in this version. Any test scores will be saved. Continue?


## 'Choose' section.

# Sub title
dashboard-choose-title = Choose

dashboard-choose-link-html = When you're done with the above, <a href="{ $url }">choose some verses or a passage to learn.</a>

## Right column.

dashboard-todays-stats-title = Today's stats

# Indicates the number of new verses the user has started today
dashboard-todays-stats-new-verses-begun = New verses begun: { $new_verses_started }

# Indicates the number of verses the user has been tested on today
dashboard-todays-stats-total-verses-tested = Total verses tested: { $total_verses_tested }

# Sub title for the list of groups the user is a member of
dashboard-your-groups-title = Your groups

# Link to see all groups the user is a member of, appears at bottom of a truncated list
dashboard-groups-see-all = (see all)

dashboard-view-other-groups-link = View other groups

dashboard-why-not-join-a-group-html = You're not in any groups yet. Why not <a href="{ $url }">join a group?</a>

## News section.

# Sub title
dashboard-news-title = News

# Link to the news page
dashboard-more-news-link = See more news...
