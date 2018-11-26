
### Learn page localizations


## Navbar:

# Link that takes the user back to the dashboard
learn-dashboard-link = Dashboard

# Link that takes the user back to where they came from
learn-return-link = Return


# This is shown in the top progress bar for a 'review' session.
learn-review-progress-bar-caption = Review:

# These are shown in the top bar when data is being saved/loaded
learn-data-working = Working…
                   .tooltip = Data transfer in progress

# Button that will attempt to re-connect with server after internet
# connection is lost.
learn-reconnect-with-server = Reconnect with server

# Displayed when recording some action failed.
# $item is a description of the action
learn-data-failed = Failed - { $item }

# Displayed when some action is in a queue
# $item is a description of the action
learn-data-in-queue = In queue - { $item }


# Displayed when attempting to record an action
# $item is a description of the action
# $attempt is the current attempt number
# $total is the total number of attempts that will be made
learn-data-being-attempted = Attempt { NUMBER($attempt) } of { NUMBER($total) } - { $item }

## Navbar - session stats info:

# Displayed before the session stats
learn-session-stats-today = Today:

# Tooltip for the 'items started today' stat
learn-items-started-today = Items started today

# Tooltip for the 'total items tested today' stat
learn-items-tested-today = Total items tested today

## Points menu:

# Displayed as a caption for the points gained in the current learning session
learn-session-points-caption = Session points:

# Tooltip for the points icon
learn-points-icon-caption = Points gained this session

## Points menu - different reasons for getting points:

learn-initial-test = initial test
learn-review-test = review test
learn-revision-completed = revision completed
learn-perfect-score-bonus = perfect score BONUS!
learn-verse-fully-learnt-bonus = verse fully learnt BONUS!
learn-award-bonus = award bonus

## Navbar:
# Tooltip for the 'pin/unpin' icon
learn-pin-icon-caption = Pin/unpin menu

# Displayed when the current user is not logged in, in place of their username
learn-guest = Guest

## Loading:

# Displayed when initially loading
learn-loading = Loading

# Displayed when initially loading, but there is first data to be saved from a previous session
learn-syncing = Syncing


## Current verse section:

# Displayed as tooltip for the memory progress percentage value
learn-memory-progress-caption = Memory progress for this verse


# Displayed as a tooltip for the toggle button that shows the previous verse
learn-toggle-show-previous-verse = Toggle show all of previous verse

learn-verse-options-icon-caption = Verse options


## Instructions section:

learn-read-text-html =
  <b>READ:</b>
  Read the text through (preferably aloud), and click '{ learn-next-button-caption }'.

learn-read-for-context-html =
  <b>READ:</b>
  Read this verse to get the context and flow of the passage.

learn-read-and-recall-html =
  <b>READ and RECALL:</b>
  Read the text through, filling in the gaps from your memory. Click a word to reveal it if you can't remember.

# Displayed when the current test is just a practice test
learn-practice-test-note-html =
  <b>PRACTICE</b> test, scores are not counted.

learn-full-word-test-html = <b>TEST:</b> Testing time! Type the text, pressing space after each word.

learn-you-dont-need-perfect-spelling = You don't need perfect spelling to get full marks.

learn-first-letter-test-html =  <b>TEST: </b> Testing time! Type the <b>first letter</b> of each word.

learn-choose-from-options-test-html = <b>TEST:</b> Testing time! For each word choose from the options shown.

# Test result.
# $score is the accuracy as a percentage.
# $comment is one of the comments below.
learn-test-result-html = <b>RESULTS</b> You scored <b>{ NUMBER($score) }</b> - { $comment }

# Comment for better than 98%
learn-test-result-awesome = awesome!

# Comment for better than 96%
learn-test-result-excellent = excellent!

# Comment for better than 93%
learn-test-result-very-good = very good.

# Comment for better than 85%
learn-test-result-good = good.

# Comment for better than 80%
learn-test-result-ok = OK.

# Comment for better than 70%
learn-test-result-could-do-better = could do better!

# Comment for less than 70%
learn-test-result-fallback = let's try again!


# Shows the progress of the verse as a percentage
# $progress is the percentage
# $direction is 'forwards' if they are making progress or 'backwards' if they went back.
# If $direction is 'backwards' then $progress is negative.
learn-verse-progress-result-html =
    <b>PROGRESS:</b>
    { $direction ->
      *[forwards]   +{ NUMBER($progress) } ↗
       [backards]    { NUMBER($progress) } ↘
    }

learn-verse-progress-complete-html =  <b>PROGRESS:</b> You reached 100% - well done!

## Action choices:

learn-next-button-caption = Next

learn-back-button-caption = Back

# Indicates a verse is fully learnt
learn-verse-fully-learnt = Fully learnt


# Displayed under 'practice' button, to indicate it will happen right now.
learn-see-again-now = Now


# Displayed when a verse will be seen again in less than 1 hour
learn-see-again-less-than-an-hour = < 1 hour

# Displayed when a verse will be seen again after between 1 and 24 hours.
# $hours is the number of hours
learn-see-again-hours = { $hours ->
                           [one]    1 hour
                          *[other]  { $hours } hours
                        }

# Displayed when a verse will be seen again after between 1 and 7 days
# $days is the number of days
learn-see-again-days = { $days ->
                           [one]    1 day
                          *[other]  { $days } days
                        }

# $weeks is the number of weeks
learn-see-again-weeks = { $weeks ->
                           [one]    1 week
                          *[other]  { $weeks } weeks
                        }

# Displayed when a verse will be seen again after several months
# $months is the number of months
learn-see-again-months = { $months ->
                           [one]    1 month
                          *[other]  { $months } months
                        }

## Verse options menu:

learn-skip-this-verse = Skip this verse for now

learn-skip-this-question = Skip this question for now

learn-stop-learning-this-verse = Stop learning this verse

learn-stop-learning-this-question = Stop learning this question

learn-reset-progress = Reset progress

learn-test-instead-of-read = Test instead of read

## Buttons under verse:

# Button for getting a hint.
# $used is the number of hints used so far,
# $total is the number of hints available,
# so it looks like "Use hint (1/2)"
learn-hint-button = Use hint ({ NUMBER($used) })/({ NUMBER($total) })

# Button used to accept and go to next verse
learn-next-button = OK

# Button used to choose to practice a verse
learn-practice = Practice

# Button used to practice a verse for a second/third time.
learn-practice-again = Practice again

# Button used to choose to see a verse sooner that normal schedule
learn-see-sooner = See sooner

## Help section:

# Link that toggles the help section to be visible
learn-help = Help
           .tooltip = Toggle help

learn-take-the-help-tour = Take the help tour.

learn-you-can-finish = You can finish your review or learning session at any
  time using the return button in the top left corner.

learn-keyboard-navigation-help = Keyboard navigation (for physical keyboards, not touchscreens):
  use Tab and Shift-Tab to move focus between controls, and Enter to 'press' one.
  Focus is shown with a colored border.

learn-button-general-help = The button for the most likely action is highlighted
  in colour and is focused by default.

# The '<a>' and '</a>' wrap the text that will become a hyperlink to change preferences
learn-you-can-change-your-testing-method-html =
    You can change your testing method at any time in your <a>preferences</a>.

# The '<a>' and '</a>' wrap the text that will become a hyperlink to change preferences
learn-on-screen-testing-not-available-html =
    On screen testing is not available for this verse in this version.
    Sorry! Please choose another option in your <a>preferences</a>


## Help tour:

# Button to finish the tour (at any point)
learn-help-tour-exit = Exit tour

# Button to go to previous step in help tour
learn-help-tour-previous = Previous

# Button to go to next step in help tour
learn-help-tour-next = Next

# Button that closes the help tour at the end
learn-help-tour-finish = Finish

learn-help-tour-hello =
    Hello! This guided tour will take you around the learning page interface.

learn-help-tour-dashboard-link =
    Use the link in the top left corner to go back to the dashboard at any time.

learn-help-tour-progress-bar =
    This bar shows your progress in learning a verse for the first time, or your total progress in a review session.

learn-help-tour-total-points =
    The total points you've earned in the current batch of verses are displayed here.

learn-help-tour-create-account =
    You need to create an account (from the link on your dashboard) to start earning points.

learn-help-tour-open-menu =
    You can tap/click this menu header to show more detail.

learn-help-tour-pin-menu =
    You can also pin this menu to the side (large screens) or the top (small screens) to have it permanently visible.

learn-help-tour-close-menu =
    Tap the menu header again to close it.

learn-help-tour-problem-saving-data =
    If there is a problem saving your data, it will be displayed here. Tap the menu header for more info.


learn-help-tour-internet-connection-cut =
    If your internet connection cuts out completely, don't worry - you can carry on working and then try to save data again when your internet connection comes back.

learn-help-tour-new-verses =
    This shows the number of new verses you have started today. If you are new to LearnScripture, it can be important to pace yourself. Why not try to learn one new verse each day?

learn-help-tour-tested-verses =
    Here is the number of verses you've been tested on today.

learn-help-tour-preferences =
    You can change your preferences at any point from here.

learn-help-tour-verse-progress =
    The approximate progress of each verse you are learning is displayed here.

learn-help-tour-verse-options =
    This menu shows additional options for the current verse.

learn-help-tour-finish-test =
    When you have finished a test, your test score is used to estimate your progress for a verse and schedule the next review. Underneath each button is a caption indicating approximately when you will next see the verse again if you choose that option.

learn-help-tour-end =
    That's all for now - thanks for taking the tour! You can take it again at any point (see the 'Help' section).

## Confirmation messages:

learn-confirm-leave-page-failed-saved =
   There is data that failed to save. If you go away from this page, the data will be lost. Do you want to continue?

learn-confirm-leave-page-save-in-progress =
   Data is still being saved.  If you go away from this page, the data will be lost. Do you want to continue?

learn-confirm-reset-progress =
   This will reset your progress on this item to zero. Continue?

## Saving data - descriptions of different data items being saved:

# Marking an item as done. $ref is a verse reference (or catechism reference)
learn-save-data-item-done = Marking done - { $ref }

# Saving score for item. $ref is a verse reference (or catechism reference)
learn-save-data-saving-score = Saving score - { $ref }

# Recording that item was read. $ref is a verse reference (or catechism reference)
learn-save-data-read-complete = Recording read - { $ref }

# Recording that item was skipped. $ref is a verse reference (or catechism reference)
learn-save-data-recording-skip = Recording skipped item - { $ref }

# Recording that an item was cancelled. $ref is a verse reference (or catechism reference)
learn-save-data-recording-cancel = Recording cancelled item - { $ref }

# Recording that progress was reset for an item. $ref is a verse reference (or catechism reference)
learn-save-data-recording-reset-progress = Resetting progress for { $ref }

# Recording that an item was marked for being reviewed sooner. $ref is a verse reference (or catechism reference)
learn-save-data-marking-review-sooner = Marking { $ref } for reviewing sooner

# Loading verses etc.
learn-loading-data = Loading items for learning...


## Error messages

# Error that normally appears only if there is an internet connection problem.
# $errorMessage gives a more specific error message.
learn-items-could-not-be-loaded-error =
    The items to learn could not be loaded (error message: { $errorMessage }). Please check your internet connection!

