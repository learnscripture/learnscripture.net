## Verse sets.

# Caption for the 'name' field of a verse set
versesets-name = Name

# Caption for the 'description' field of verse sets
versesets-description = Description

# Caption for the 'additional info' field of verse sets
versesets-additional-info = Additional info

# Caption for the 'public' field when creating a Verse Set
versesets-public = Make public (can't be undone)

# Caption for the 'language' field of verse sets.
versesets-language = Language
                   .help-text = The language used in the ‘{ versesets-name }’, ‘{ versesets-description}’ and ‘{ versesets-additional-info }’ fields.

## Searching and filtering verse sets.

# Caption for the search input box for searching for verse sets
versesets-search = Search

# Caption for the filter to select type of verse set (selection or passage)
versesets-filter-type = Type

# Caption for filtering by 'Selection' verse sets
versesets-filter-selection-caption = Selection - hand-picked verses usually on a theme or topic

# Caption for filtering by 'Passage' verse sets
versesets-filter-passage-caption = Passage - continuous verses in a chapter

# Caption for showing all verse set types (selection and passage)
versesets-filter-all = All

# Caption for the sorting options of the verse sets
versesets-order = Order

# Caption for ordering verse sets by most popular first
versesets-order-most-popular-first = Most popular first

# Caption for ordering verse sets by newest first
versesets-order-newest-first = Newest first



## Viewing a verse set.

# Page title.
# $name is the name of the verse set being viewed.
versesets-view-set-page-title = Verse set: { $name }

# Sub-title for list of verses in set
versesets-view-set-verses-title = Verses

# Message displayed when verse set is empty
versesets-view-set-no-verses = No verses in this set!



# Sub-title for additional notes about the verse set
versesets-view-set-notes-title = Notes

# Note about how to opt out of learning
versesets-view-set-how-to-opt-out = When learning a set, you can opt out of any individual verse by pressing
          ‘{ learn-stop-learning-this-verse }’ on the learning page.

# Note about verse set being public
versesets-view-set-learning-is-public = Learning a verse set is a public action
        (unless the set is private and remains private)

# Prompt to change a verse set to a 'passage set'
versesets-view-set-change-to-passage-set = This looks like a continuous set of verses. These are much better learned
      using a 'passage' set, rather than a 'selection' set. You can convert using
      the button below:

# Button to change to passage set
versesets-view-set-change-to-passage-set-button = Convert to passage set


# Notice displayed when a 'selection' verse set is converted to a 'passage' verse set
versesets-converted-to-passage = Verse set converted to 'passage' type

# Button to edit the verse set being displayed
versesets-view-set-edit-button = Edit

# Sub-title for section with additional info about the verse set
versesets-view-set-info-title = Verse set info

# Indicates who put the verse set together.
versesets-view-set-put-together-by-html = Put together by { $username }

# Indicates when the verse set was created
versesets-view-set-date-created = Created on { DATETIME($date_created) }.

# Shown when the verse set is private
versesets-view-set-private = Private - this verse set can only be accessed by you.

# Sub-title for section about the user's use of this verse set
versesets-view-set-status-title = Status

# Shown when the user isn't learning the verse set at all (in the given Bible version).
# $version_name is the name of a Bible version.
versesets-view-set-not-learning = You are not learning this verse set in { $version_name }.

# Shown when the user has started learning all the verses in the verse set.
# $version_name is the name of a Bible version.
versesets-view-set-learning-all = You've started learning all the verses in this set in { $version_name }.

# Shown when the user has started learning some of the verses in the verse set.
# $started_count is the number they have started learning.
# $total_count is the total number of verses in the set.
# $version_name is the name of a Bible version.
versesets-view-set-learning-some = You've started learning { $started_count } out of { $total_count } verses in this set in version { $version_name }.

# Shown when the user has some verses in this set in their learning queue.
# $in_queue_count is the number of verses in their queue.
# $version_name is the name of a Bible version.
versesets-view-set-number-in-queue = You have { $in_queue_count ->
     [one]      1 verse
    *[other]    { $in_queue_count } verses
 } from this set in your queue for learning in version { $version_name }.

# Beginning of section regarding removing verses from learning queue
versesets-view-set-remove-from-queue-start = If you want to remove them:

# First method for removing verses from queue
versesets-view-set-remove-from-queue-method-1 =
        remove them individually from the learning interface by choosing
        '{ learn-stop-learning-this-verse }'
        from the verse options menu when the verse comes up for learning.

# Second method for removing verses from queue, followed by a button to remove all
versesets-view-set-remove-from-queue-method-2 = Or you can remove them all:

# Button to drop all verses from queue
versesets-view-set-drop-from-queue-button = Drop from queue

# Noticed displayed after the user chooses to remove some verses from their learning queue
versesets-dropped-verses = Dropped { $count ->
    [one]   one verse
   *[other] { $count } verses
 } from your learning queue.


## Creating/editing verse sets.

# Page title for editing
versesets-edit-set-page-title = Edit verse set

# Page title for creating a selection set
versesets-create-selection-page-title = Create selection set

# Page title for creating a passage set
versesets-create-passage-page-title = Create passage set

# Sub title when editing verse sets, for title/description fields
versesets-about-set-fields = About this set

# Sub title when editing verse sets, for list of verses in set
versesets-verse-list = Verse list

# Message displayed in verses when no verses have been added yet
versesets-no-verses-yet = No verses added yet!

# Validation error message if user tries to create set with no verses
versesets-no-verses-error = No verses in set

# Success message when a verse set is saved
versesets-set-saved = Verse set '{ $name }' saved!

# Sub title for the section with controls for adding verses
versesets-add-verses-subtitle = Add verses

# Caption on button for adding a verse to a verse set
versesets-add-verse-to-set = Add to set

# Caption for the button that saves the edited/new verse set
versesets-save-verseset-button = Save verse set

# Sub title for section that allows you to choose a passage
versesets-choose-passage = Choose passage

versesets-natural-break-explanation =
  For passages more than about 10 verses, it helps if you can indicate the
  natural breaks in the passage by ticking the 'Section break' box on the verses
  which start a new section or paragraph.

# Explanation of 'breaks'
versesets-natural-break-explanation-part-2-html =
  <b>NOTE:</b> section breaks are in <b>addition</b> to verse breaks to indicate <b>larger</b> sections.
  When learning, you will only ever be presented with one verse at a time, even if you do not add
  section breaks.

# Heading for section break column
versesets-section-break = Section break

# Sub title for section with optional fields
versesets-optional-info = Optional extra info

# Shown when the user enters a passage reference and there are other verse sets for that passage
versesets-create-duplicate-passage-warning = There are already some passage sets for this passage:

## Viewing user's own verse sets.

# Sub-title for section showing the list of verse sets the user is learning
versesets-you-are-learning-title = Verse sets you are learning

# Sub-title for section showing the list of verse sets the user created
versesets-you-created-title = Verse sets you created
