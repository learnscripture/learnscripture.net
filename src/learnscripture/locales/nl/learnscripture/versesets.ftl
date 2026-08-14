## Verse sets.

# Caption for the 'name' field of a verse set
versesets-name = Naam

# Caption for the 'description' field of verse sets
versesets-description = Omschrijving

# Caption for the 'additional info' field of verse sets
versesets-additional-info = Aanvullende informatie

# Caption for the 'public' field when creating a Verse Set
versesets-public = openbaar maken (kan niet ongedaan worden gemaakt)

# Caption for the 'language' field of verse sets.
versesets-language = Taal
                   .help-text = De taal gebruikt in de ‘{ versesets-name }’, ‘{ versesets-description}’ en ‘{ versesets-additional-info }’ velden.

## Searching and filtering verse sets.

# Caption for the search input box for searching for verse sets
versesets-search = Zoek

# Caption for the filter to select type of verse set (selection or passage)
versesets-filter-type = Type

# Caption for filtering by 'Selection' verse sets
versesets-filter-selection-caption = Selectie - zelfgekozen verzen, meestal over een thema of onderwerp

# Caption for filtering by 'Passage' verse sets
versesets-filter-passage-caption = Passage - opeenvolgende verzen in een hoofdstuk

# Caption for showing all verse set types (selection and passage)
versesets-filter-all = Alle

# Caption for the sorting options of the verse sets
versesets-order = Volgorde

# Caption for ordering verse sets by most popular first
versesets-order-most-popular-first = Meest populaire eerst

# Caption for ordering verse sets by newest first
versesets-order-newest-first = Nieuwste eerst



## Viewing a verse set.

# Page title.
# $name is the name of the verse set being viewed.
versesets-view-set-page-title = Verzenserie: { $name }

# Sub-title for list of verses in set
versesets-view-set-verses-title = Verzen

# Message displayed when verse set is empty
versesets-view-set-no-verses = Geen verzen in deze serie!



# Sub-title for additional notes about the verse set
versesets-view-set-notes-title = Opmerkingen

# Note about how to opt out of learning
versesets-view-set-how-to-opt-out = Als je een serie leert, kun je individuele verzen uitselecteren door op
          ‘{ learn-stop-learning-this-verse }’ op de leerpagina te klikken.

# Note about verse set being public
versesets-view-set-learning-is-public = Een verzenserie leren is een openbaare actie
        (tenzij de serie privé is en blijft)

# Prompt to change a verse set to a 'passage set'
versesets-view-set-change-to-passage-set = Dit ziet eruit als een serie opeenvolgende verzen. Deze zijn makkelijker te leren
      door gebruik te maken van een 'passage'-serie in plaats van een 'selectie'-serie.
      Om de serie om te zetten, klik op de knop hieronder:

# Button to change to passage set
versesets-view-set-change-to-passage-set-button = Omzetten naar passage-serie


# Notice displayed when a 'selection' verse set is converted to a 'passage' verse set
versesets-converted-to-passage = Verzenserie is omgezet naar type 'passage'

# Button to edit the verse set being displayed
versesets-view-set-edit-button = Aanpassen

# Sub-title for section with additional info about the verse set
versesets-view-set-info-title = Verzenserie informatie

# Indicates who put the verse set together.
versesets-view-set-put-together-by-html = Samengesteld door { $username }

# Indicates when the verse set was created
versesets-view-set-date-created = Gemaakt op { DATETIME($date_created) }.

# Shown when the verse set is private
versesets-view-set-private = Privé - deze verzenserie is alleen toegankelijk voor jou.

# Sub-title for section about the user's use of this verse set
versesets-view-set-status-title = Status

# Shown when the user isn't learning the verse set at all (in the given Bible version).
# $version_name is the name of a Bible version.
versesets-view-set-not-learning = Je leert deze verzenserie niet in de { $version_name }.

# Shown when the user has started learning all the verses in the verse set.
# $version_name is the name of a Bible version.
versesets-view-set-learning-all = Je bent begonnen alle verzen in deze serie te leren in de { $version_name }.

# Shown when the user has started learning some of the verses in the verse set.
# $started_count is the number they have started learning.
# $total_count is the total number of verses in the set.
# $version_name is the name of a Bible version.
versesets-view-set-learning-some = Je bent begonnen { $started_count } van de { $total_count } verzen in deze serie in de { $version_name } te leren.

# Shown when the user has some verses in this set in their learning queue.
# $in_queue_count is the number of verses in their queue.
# $version_name is the name of a Bible version.
versesets-view-set-number-in-queue = Je hebt { $in_queue_count ->
     [one]      1 vers
    *[other]    { $in_queue_count } verzen
 } van deze serie in je wachtrij staan.

# Beginning of section regarding removing verses from learning queue
versesets-view-set-remove-from-queue-start = Als je ze uit je wachtrij wilt verwijderen:

# First method for removing verses from queue
versesets-view-set-remove-from-queue-method-1 =
        verwijder individuele verzen van het leeroverzicht door te kiezen voor
        '{ learn-stop-learning-this-verse }'
        uit het menu voor versopties als het vers in het leeroverzicht komt.

# Second method for removing verses from queue, followed by a button to remove all
versesets-view-set-remove-from-queue-method-2 = Of je kunt alle verzen uit de wachtrij verwijderen:

# Button to drop all verses from queue
versesets-view-set-drop-from-queue-button = Verwijderen uit wachtrij

# Noticed displayed after the user chooses to remove some verses from their learning queue
versesets-dropped-verses = { $count ->
    [one]   1 vers
   *[other] { $count } verzen
 } uit je wachtrij verwijderd.


## Creating/editing verse sets.

# Page title for editing
versesets-edit-set-page-title = Verzenserie aanpassen

# Page title for creating a selection set
versesets-create-selection-page-title = Selectie-serie maken

# Page title for creating a passage set
versesets-create-passage-page-title = Passage-serie maken

# Sub title when editing verse sets, for title/description fields
versesets-about-set-fields = Over deze serie

# Sub title when editing verse sets, for list of verses in set
versesets-verse-list = Verzenlijst

# Message displayed in verses when no verses have been added yet
versesets-no-verses-yet = Nog geen verzen toegevoegd!

# Validation error message if user tries to create set with no verses
versesets-no-verses-error = Geen verzen in serie

# Success message when a verse set is saved
versesets-set-saved = Verzenserie '{ $name }' opgeslagen!

# Sub title for the section with controls for adding verses
versesets-add-verses-subtitle = Vers toevoegen

# Caption on button for adding a verse to a verse set
versesets-add-verse-to-set = Toevoegen aan serie

# Caption for the button that saves the edited/new verse set
versesets-save-verseset-button = Verzenserie opslaan

# Sub title for section that allows you to choose a passage
versesets-choose-passage = Kies passage

versesets-natural-break-explanation =
  Voor passages met meer dan 10 verzen helpt het om deze onder te verdelen in secties.
  Dit kan door in de passage bij het beginvers van een nieuwe sectie of paragraaf het vakje 'Sectiebreuk'
  te selecteren.

# Explanation of 'breaks'
versesets-natural-break-explanation-part-2-html =
  <b>OPMERKING:</b> Sectiebreuken zijn een <b>aanvulling</b> op versbreuken om <b>grotere</b> secties aan te geven.
  Als je aan het leren bent zal je maar om één vers tegelijkertijd gevraagd worden, zelfs als je geen sectiebreuken toevoegt.

# Heading for section break column
versesets-section-break = Sectiebreuk

# Sub title for section with optional fields
versesets-optional-info = Optionele extra informatie

# Shown when the user enters a passage reference and there are other verse sets for that passage
versesets-create-duplicate-passage-warning = Er zijn al een paar passage-series van deze passage:

## Viewing user's own verse sets.

# Sub-title for section showing the list of verse sets the user is learning
versesets-you-are-learning-title = Verzenseries die je aan het leren bent

# Sub-title for section showing the list of verse sets the user created
versesets-you-created-title = Verzenseries die je gemaakt hebt
