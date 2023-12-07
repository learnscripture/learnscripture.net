
### Learn page:

# Page title
learn-page-title = Leren


## Navbar:

# Link that takes the user back to the dashboard
learn-dashboard-link = Dashboard

# Link that takes the user back to where they came from
learn-return-link = Terug


# This is shown in the top progress bar for a 'review' session.
learn-review-progress-bar-caption = Herhalen:

# These are shown in the top bar when data is being saved/loaded
learn-data-working = Bezig…
                   .tooltip = Dataoverdracht is bezig

# Button that will attempt to re-connect with server after internet
# connection is lost.
learn-reconnect-with-server = Verbind opnieuw met de server

# Displayed when recording some action failed.
# $item is a description of the action
learn-data-failed = Mislukt - { $item }

# Displayed when some action is in a queue
# $item is a description of the action
learn-data-in-queue = In wachtrij - { $item }


# Displayed when attempting to record an action
# $item is a description of the action
# $attempt is the current attempt number
# $total is the total number of attempts that will be made
learn-data-being-attempted = Poging { NUMBER($attempt) } van { NUMBER($total) } - { $item }

## Navbar - session stats info:

# Displayed before the session stats
learn-session-stats-today = Vandaag:

# Tooltip for the 'items started today' stat
learn-items-started-today = Vandaag begonnen items

# Tooltip for the 'total items tested today' stat
learn-items-tested-today = Totaal vandaag geteste items

## Points menu:

# Displayed as a caption for the points gained in the current learning session
learn-session-points-caption = Punten deze sessie:

# Tooltip for the points icon
learn-points-icon-caption = Punten behaald in deze sessie

## Points menu - different reasons for getting points:

learn-initial-test = eerste test
learn-review-test = herhalingstest
learn-revision-completed = herhaling voltooid
learn-perfect-score-bonus = perfecte score BONUS!
learn-verse-fully-learned-bonus = vers volledig geleerd BONUS!
learn-award-bonus = troffeebonus

## Navbar:
# Tooltip for the 'pin/unpin' icon
learn-pin-icon-caption = Zet menu vast

# Displayed when the current user is not logged in, in place of their username
learn-guest = Gast

## Loading:

# Displayed when initially loading
learn-loading = Laden...

# Displayed when initially loading, but there is first data to be saved from a previous session
learn-syncing = Synchroniseren...


## Current verse section:

# Displayed as tooltip for the memory progress percentage value
learn-memory-progress-caption = Voortgang voor dit vers


# Displayed as a tooltip for the toggle button that shows the previous verse
learn-toggle-show-previous-verse = Toon volledige vorige vers

learn-verse-options-icon-caption = Opties voor dit vers


## Instructions section:

learn-read-text-html =
  <b>LEES:</b>
  Lees de tekst (hardop, indien mogelijk), en klik '{ learn-next-button-caption }'.

learn-read-for-context-html =
  <b>LEES:</b>
  Lees dit vers voor de context en de loop van het verhaal.

learn-read-and-recall-html =
  <b>LEES en HERINNER:</b>
  Lees de tekst door, en vul de gaten uit je geheugen. Klik op een woord om het te laten zien als je het je niet kunt herinneren.

# Displayed when the current test is just a practice test
learn-practice-test-note-html =
  <b>PRACTICE</b> test, score wordt niet meegerekend.

learn-full-word-test-html = <b>TOETS:</b> Tijd voor een test! Typ de tekst en druk op de spatiebalk na elk woord.

learn-you-dont-need-perfect-spelling = De spelling hoeft niet perfect te zijn om volledige punten te krijgen.

learn-first-letter-test-html =  <b>TOETS: </b> Tijd voor een test! Typ de <b>eerste letter</b> van elk woord.

learn-choose-from-options-test-html = <b>TOETS:</b> Tijd voor een test! Kies uit de getoonde opties voor elk woord.

# Test result.
# $score is the accuracy as a percentage.
# $comment is one of the comments below.
learn-test-result-html = <b>RESULTATEN</b> Je hebt <b>{ NUMBER($score) }</b> goed - { $comment }

# Comment for better than 98%
learn-test-result-awesome = Geweldig!

# Comment for better than 96%
learn-test-result-excellent = Fantastisch!

# Comment for better than 93%
learn-test-result-very-good = Heel goed.

# Comment for better than 85%
learn-test-result-good = Goed.

# Comment for less than 85%, or when we are suggesting to try again.
learn-test-result-try-again = laten we het opnieuw proberen!


# Shows the progress of the verse as a percentage
# $progress is the percentage
# $direction is 'forwards' if they are making progress or 'backwards' if they went back.
# If $direction is 'backwards' then $progress is negative.
learn-verse-progress-result-html =
    <b>VOORTGANG:</b>
    { $direction ->
      *[forwards]   +{ NUMBER($progress) } ↗
       [backwards]   { NUMBER($progress) } ↘
    }

learn-verse-progress-complete-html =  <b>VOORTGANG:</b> Je hebt 100% behaald - Goed zo!

## Action choices:

learn-next-button-caption = Volgende

learn-back-button-caption = Vorige

# Indicates a verse is fully learned
learn-verse-fully-learned = Volledig geleerd


# Displayed under 'practice' button, to indicate it will happen right now.
learn-see-again-now = Nu


# Displayed when a verse will be seen again in less than 1 hour
learn-see-again-less-than-an-hour = < 1 uur

# Displayed when a verse will be seen again after between 1 and 24 hours.
# $hours is the number of hours
learn-see-again-hours = { $hours ->
                           [one]    1 uur
                          *[other]  { $hours } uur
                        }

# Displayed when a verse will be seen again after between 1 and 7 days
# $days is the number of days
learn-see-again-days = { $days ->
                           [one]    1 dag
                          *[other]  { $days } dagen
                        }

# $weeks is the number of weeks
learn-see-again-weeks = { $weeks ->
                           [one]    1 week
                          *[other]  { $weeks } weken
                        }

# Displayed when a verse will be seen again after several months
# $months is the number of months
learn-see-again-months = { $months ->
                           [one]    1 maand
                          *[other]  { $months } maanden
                        }

## Verse options menu:

learn-skip-this-verse = Sla dit vers over voor nu

learn-skip-this-question = sla deze vraag over voor nu

learn-stop-learning-this-verse = Stop met het leren van dit vers

learn-stop-learning-this-question = Stop met het leren van deze vraag

learn-reset-progress = Voortgang resetten

learn-test-instead-of-read = Test in plaats van lezen

## Buttons under verse:

# Button for getting a hint.
# $used is the number of hints used so far,
# $total is the number of hints available,
# so it looks like "Use hint (1/2)"
learn-hint-button = Gebruik hint ({ NUMBER($used) }/{ NUMBER($total) })

# Button used to accept and go to next verse
learn-next-button = OK

# Button used to choose to practice a verse
learn-practice = Oefenen

# Button used to practice a verse for a second/third time.
learn-practice-again = Opnieuw oefenen

# Button used to choose to see a verse sooner that normal schedule
learn-see-sooner = Zie eerder

## Help section:

# Link that toggles the help section to be visible
learn-help = Help
           .tooltip = Zet hulp aan of uit

learn-take-the-help-tour = Rondleiding.

learn-you-can-finish = Je kunt je leer- of herhaalsessie op elk moment stoppen
    met de terugknop in de linker bovenhoek.

learn-keyboard-navigation-help = Toetsenbordnavigatie (voor toetsenborden, niet touchscreens):
  gebruik Tab en Shift-Tab om knoppen te selecteren, en Enter om een knop in te drukken.
  Je selectie is zichtbaar door de gekleurde rand.

learn-button-general-help = De meest logische knop is standaard geselecteerd.

# The '<a>' and '</a>' wrap the text that will become a hyperlink to change preferences
learn-you-can-change-your-testing-method-html =
    Je kunt op elk moment je toestmethode veranderen in je <a>voorkeuren</a>.

# The '<a>' and '</a>' wrap the text that will become a hyperlink to change preferences
learn-on-screen-testing-not-available-html =
    Meerkeuzetests zijn niet beschikbaar voor dit vers in deze vertaling.
    Sorry! Kies een andere optie in je <a>voorkeuren</a>.
## Help tour:

# Button to finish the tour (at any point)
learn-help-tour-exit = Rondleiding verlaten

# Button to go to previous step in help tour
learn-help-tour-previous = Vorige

# Button to go to next step in help tour
learn-help-tour-next = Volgende

# Button that closes the help tour at the end
learn-help-tour-finish = Voltooien

# First message shown in help tour
learn-help-tour-hello =
    Hallo! Deze rondleiding leidt je langs alle onderdelen van je leeroverzicht

learn-help-tour-dashboard-link =
    Gebruik de link in de linker bovenhoek om terug te gaan naar het dashboard.

learn-help-tour-progress-bar =
    Deze balk toont je voortgang als je een vers voor het eerst leert, of je totale voortgang in een herhalingssessie.

learn-help-tour-total-points =
    Hier zie je het totaalaantal punten dat je met de huidige set verzen behaald hebt.

learn-help-tour-create-account =
    Je moet een account aanmaken (via de link op je dashboard) om punten te verdienen.

learn-help-tour-open-menu =
    Je kunt op deze menukop klikken om meer details te laten zien.

learn-help-tour-pin-menu =
    Je kunt dit menu vastzetten aan de zijkant (op grote schermen) of bovenin (op kleine schermen) om het altijd zichtbaar te hebben.

learn-help-tour-close-menu =
    Klik de opnieuw op de menukop om het menu weer te sluiten.

learn-help-tour-problem-saving-data =
    Als er een probleem is bij het opslaan van je gegevens, staat dat heir. Klik op de menuheader voor meer informatie.


learn-help-tour-internet-connection-cut =
    Als je internetverbinding verbroken wordt, is er niets aan de hand - je kunt gewoon doorwerken en je gegevens weer opslaan als je internetverbinding terugkomt.

learn-help-tour-new-verses =
    Hier staat hoeveel verzen je vandaag begonnen bent te leren. Als je nieuw bent bij LearnScrripture, is het belangrijk om een gezond tempo aan te houden. Waarom begin je niet met een nieuw vers per dag?

learn-help-tour-tested-verses =
    Hier is hoeveel verzen vandaag overhoord zijn.

learn-help-tour-preferences =
    Je kunt hier altijd je voorkeuren aanpassen.

learn-help-tour-verse-progress =
    Hier zie je een schatting van je voortgang bij het leren van elk vers.

learn-help-tour-verse-options =
    Dit menu geeft extra opties voor het huidige vers.

learn-help-tour-finish-test =
    Als je een test voltooid hebt, wordt je testscore gebruikt om je voortgang bij een vers te schatten, en wordt je volgende herhaling klaargezet.
    Onder elke knop zie je wanneer je dit vers terugziet als je die optie kiest.

learn-help-tour-end =
    Dat was het voor nu - bedankt voor het volgen van de rondleiding! Je kunt de rondleiding opnieuw volgen wanneer je maar wilt. (Zie de 'Help' knop.)

## Confirmation messages:

learn-confirm-leave-page-failed-saved =
    Het opslaan van de data is mislukt. Als je deze pagina nu verlaat, gaat deze data verloren. Wil je toch de pagina verlaten?

learn-confirm-leave-page-save-in-progress =
    We zijn nog bezig je data op te slaan. Als je deze pagina nu verlaat, gaat deze data verloren. Wil je toch de pagina verlaten?

learn-confirm-reset-progress =
    Dit zet je voortgang op dit punt terug naar nul. Wil je toch doorgaan?

## Saving data - descriptions of different data items being saved:

# Marking an item as done. $ref is a verse reference (or catechism reference)
learn-save-data-item-done = { $ref } als klaar markeren

# Saving score for item. $ref is a verse reference (or catechism reference)
learn-save-data-saving-score = Score aan het opslaan voor { $ref }

# Recording that item was read. $ref is a verse reference (or catechism reference)
learn-save-data-read-complete = { $ref } markeren als gelezen

# Recording that item was skipped. $ref is a verse reference (or catechism reference)
learn-save-data-recording-skip = { $ref } markeren als overgeslagen

# Recording that an item was cancelled. $ref is a verse reference (or catechism reference)
learn-save-data-recording-cancel = { $ref } markeren als geannuleerd

# Recording that progress was reset for an item. $ref is a verse reference (or catechism reference)
learn-save-data-recording-reset-progress = Voortgang aan het resetten voor { $ref }

# Recording that an item was marked for being reviewed sooner. $ref is a verse reference (or catechism reference)
learn-save-data-marking-review-sooner = { $ref } wordt eerder herhaald

# Loading verses etc.
learn-loading-data = Items aan het laden om te leren...


## Error messages

# Error that normally appears only if there is an internet connection problem.
# $errorMessage gives a more specific error message.
learn-items-could-not-be-loaded-error =
    De items om te leren konden niet geladen worden (error message: { $errorMessage }). Controleer je internetverbinding!
