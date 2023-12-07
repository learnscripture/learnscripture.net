### Dashboard page
# Title of 'dashboard' page
dashboard-page-title = Dashboard

# Notice that appears for guest users who haven't created an account yet
dashboard-remember-to-create-an-account-html =
    <b>Vergeet niet om <a href="{ $signup_url }">een account aan te maken</a></b> -
    anders gaat je voortgang verloren! Een account aanmaken is gratis, duurt slechts       enkele seconden en geeft je toegang tot extra opties zoals trofeeën, groepen, een      leaderboard en statitieken. Als gast gaat je data verloren op { DATETIME($expires) }.


## Unfinished session section.

# Sub title
dashboard-continue-title =
    Doorgaan

dashboard-unfinished-notice = Je hebt een niet afgeronde oefensessie open staan.

dashboard-unfinished-notice-part-2 = Ga door met de sessie om niet opgeslagen data te synchroniseren.

# Caption for button that will continue the session
dashboard-continue-button = Doorgaan

## Heatmap section.

dashboard-learning-events = Gebeurtenissen

## Review section.

# Sub title
dashboard-review-title = Test

# Button for reviewing a whole passage
dashboard-review-whole-passage-button = Hele passage

# Button for reviewing one section of a passage.
# $verse_count is the number of verses in that section.
dashboard-review-one-section-button = Eén sectie ({ $verse_count } verzen)

# Button for reviewing a verse or set of verses, or a catechism question
dashboard-review-button = Test

# Button for cancelling learning a verse/passage
dashboard-cancel-learning = Annuleren

# Note shown when the whole passage is due for review
# $verse_count is the number of verses in the passage
dashboard-passage-due-for-review = Deze passage kan worden getest  ({ $verse_count } verzen).

# Note shown when part of a passage verse set is due for review.
# $needs_testing_count is the number that are due for review,
# $total_verse_count is the total number of verses in the passage
dashboard-passage-part-due-for-review = Een deel van deze passage kan getest worden ({ $needs_testing_count }/{ $total_verse_count } verzen).

# Indicates the number of verses due for review (separate from the passage verse sets)
dashboard-verses-for-review-count = Momenteel
  { $count ->
    [one]     kan er 1 vers
   *[other]  kunnen er { $count } verzen
  } getest worden.

# Displayed before a list of verse references that are due for review or learning
dashboard-verses-coming-up = Volgende verzen:

# Indicates the number of catechism questions due for review
dashboard-catechism-questions-for-review-count = Momenteel kan je { $count } vragen testen.

# Message shown if there is nothing in the general queue due for reviewing. (Excludes passage verse sets)
dashboard-general-queue-empty = Er zijn geen verzen of vragen die op dit moment getest moeten worden.

# Message about the next verse due for review.
# $title is the verse reference or catechism title,
# $timeuntil is a string like "5 minutes" or "3 hours"
dashboard-next-item-due-html = Het volgende vers dat getest wordt: <b>{ $title }</b> over { $timeuntil }


## Learn section.

# Sub title
dashboard-learn-title = Leren

# Button to start learning a passage
dashboard-learn-start-learning-button = Begin met leren

# Button to continue learning a passage (they have already started at least one verse)
dashboard-learn-continue-learning-button = Ga verder met leren

# Message displayed for a passage set that is in the user's queue
# for learning (but that haven't started yet)
dashboard-passage-queued = Je hebt deze passage geselecteerd om te leren.

# Message on a passage verse set indicating the number of items learned
# and still not started.
dashboard-passages-youve-seen-verses =
    Je hebt tot nu toe { $tested_total ->
            [1]     1 vers
           *[other] { $tested_total } verzen
     } geleerd,
     met nog { $untested_total } te gaan.

# Message on a passage verse set indicating the number of items learned
# and still not started, inluding info about those that are due for review.
dashboard-passages-youve-seen-verses-with-review-due-html =
    Je hebt tot nu toe in { $tested_total ->
            [1]     1 vers
           *[other] { $tested_total } verzen
     } geleerd,
    <b>{ $needs_review_total } klaar om te testen</b>,
    met nog { $untested_total } te gaan.


# Sub title for verses that aren't part of a verse set
dashboard-learn-other-verses = Andere verzen

# Shows number of verses in queue for learning
dashboard-queued-verses = Je hebt { $count } verzen in de rij gezet om te leren.

# Shows number of verses in a particular set in queue for learning
dashboard-queued-verses-in-set = Je hebt { $count } verzen in de rij gezet om in deze serie te leren.

# Button to learn a verse or queue of verses
dashboard-learn-button = Begin met leren

# Button to remove items from the queue of verses to learn
dashboard-clear-queue-button = Annuleren

# Indicates the total number of questions in a catechism that has been queued for learning
dashboard-catechism-question-count = Je bent begonnen met het leren van deze catechismus, in totaal { $count } vragen.

# Indicates the number of questions in a catechism that have been started, and how many remain.
dashboard-catechism-learned-and-remanining-count = Je hebt tot nu toe
   { $started_count ->
       [one]     1 vraag
      *[other]   { $started_count } vragen
   } geleerd,
   met nog { $remaining_count } te gaan.

# Message displayed when there are no passages, verses or catechisms queued for learning
dashboard-learn-nothing-in-queue = Er staat niets in de wachtrij om te leren.

# Confirmation prompt after clicking 'clear queue' button for verses
dashboard-remove-verses-from-queue-confirm = Dit verwijdert het gekozen vers of de gekozen verzen uit de wachtrij. Als je dit wil herstellen, moet je het vers of de verzenserie opnieuw selecteren. Wil je doorgaan?

# Confirmation prompt after clicking 'cancel' button for a catechism
dashboard-remove-catechism-from-queue = Dit verwijdert de gekozen catechismusvragen uit de leerwachtrij. Als je ze opnieuw wilt leren, moet je de catechismus opnieuw selecteren. Wil je doorgaan?

# Confirmation prompt after clicking 'cancel' for a passage verse set
dashboard-cancel-passage-confirm = Dit verwijdert deze passage uit je wachtrij met te leren verzen. Testscores blijven behouden. Wil je doorgaan?


## 'Choose' section.

# Sub title
dashboard-choose-title = Kiezen

dashboard-choose-link-html = Als je de bovenstaande teksten hebt geleerd, <a href="{ $url }">kun je hier nieuwe verzen of passages kiezen om uit je hoofd te leren.</a>

## Right column.

dashboard-todays-stats-title = Statistieken van vandaag

# Indicates the number of new verses the user has started today
dashboard-todays-stats-new-verses-begun = Nieuw begonnen verzen: { $new_verses_started }

# Indicates the number of verses the user has been tested on today
dashboard-todays-stats-total-verses-tested = Geteste verzen: { $total_verses_tested }

# Sub title for the list of groups the user is a member of
dashboard-your-groups-title = Jouw groepen

# Link to see all groups the user is a member of, appears at bottom of a truncated list
dashboard-groups-see-all = (see all)

dashboard-view-other-groups-link = Bekijk andere groepen

dashboard-why-not-join-a-group-html = Je zit nog niet in een groep. <a href="{ $url }">Wil je lid worden van een groep?</a>

## News section.

# Sub title
dashboard-news-title = Nieuws

# Link to the news page
dashboard-more-news-link = Bekijk meer nieuws...
