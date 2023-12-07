## Awards/badges.

# Notification received when a user gets a new award/badge,
# $award is the award name (appears as a link)
awards-new-award-html = Je hebt een nieuwe trofee verdiend: { $award }.

# Notification received when a user gets a higher level for an award/badge
# $award is the award name (appears as a link)
awards-levelled-up-html = Een van je trofeeën is een level gestegen: { $award }.

# Notification when there are points for an award that has been received.
# $points is the number of points given
awards-points-bonus =  Bonuspunten: { $points }.

# Appears next to notification about new award, as shortcuts for
# telling other people about the award.
# $twitter is a link to Twitter.
awards-tell-people-html = Vertel het je vrienden: { $twitter }

# Default message that is used for sharing about awards on social media
# $award is the award name/description
awards-social-media-default-message = Ik heb zojuist een trofee verdiend: { $award }

## Awards page.

# Page title
awards-page-title = Trofeeën

awards-the-following-are-available = Je kunt de volgende trofeeën halen:


# Caption in table header for award name/icon
awards-award = Trofee

# Caption in table header for when the award was received
awards-date-received = Datum

# Caption in table header for award icon
awards-icon = Icoon

# Caption in table header for award description
awards-description = Beschrijving

# Caption in the table header for award points
awards-points = Punten

# Indicates the level of an award/badge
awards-award-level = Level { $level }

# Indicates the highest level that has so been achieved for the award
award-highest-level-achieved-html = Hoogste level tot nu toe bereikt: <b>Level { $level }</b>

# Link to page showing details about who has achieved the award,
# $name is the name/short description of the award
award-people-with-award = Mensen met { $name }-trofee



## Individual award page.

# Page title,
# $name is the award name/short description
awards-award-page-title = Trofee - { $name }

# Heading for description of award
awards-description-subtitle = Beschrijving

# Heading for list of people who have achieved the award
awards-achievers-subtitle = Mensen die deze trofee bezittenZ

# Indicates the highest level that can be achieved for an award
awards-award-highest-level = Level { $level } is het hoogste level.

# Subtitle
awards-level-subtitle = Level { $level }

# Indicates the number of people who have achieved the award at this level, followed
# by a list containing all those users
awards-level-achievers-all = Totaal { $count ->
    [one]    1 gebruiker
   *[other]  { $count } gebruikers
 }:

# Indicates the number of people who have achieved the award at this level, followed
# by a list containing a sample of those users.
awards-level-achievers-truncated = Totaal { $count ->
    [one]    1 gebruiker
   *[other]  { $count } gebruikers
 }, including:


# Link to page showing all badges
awards-all-available-badges = Alle beschikbare trofeeën

# Link to page showing user's badges
awards-your-badges = Jouw trofeeën

# Subtitle for section describing the user's level for the award being described
awards-your-level = Jouw level

# Used when the award has levels, and the user has the award at a certain level
awards-you-have-this-award-at-level = Je hebt deze trofee, met level { $level }.

# Used when the award has does not have levels, and the user has the award.
awards-you-have-this-award = Je hebt deze trofee.

# Used when the user doesn't have the award
awards-you-dont-have-this-award = Je hebt deze trofee nog niet.

# Message used when trying to view some old awards
awards-removed = De ‘{ $name }’-trofee wordt niet meer uitgereikt

## 'Student' award.

# Name
awards-student-award-name = Student

# General description
awards-student-award-general-description = Uitgereikt voor het starten met verzen leren. Level 1 is voor 1 vers, level 9 voor de hele Bijbel.

# Description for a specific level
awards-student-award-level-n-description = Leer minimaal { $verse_count ->
    [one]    1 vers
   *[other]  { $verse_count } verzen
 }

# Specific description for level 9
awards-student-award-level-9-description = Leer de hele Bijbel!

## 'Master' award.

# Name
awards-master-award-name = Master

# General description
awards-master-award-general-description =
   Uitgereikt voor het volledig leren van verzen. Dit duurt normaliter ongeveer een jaar, zodat je zeker weet dat je je het vers voor altijd goed herinnert. Level 1 is voor 1 vers, level 9 voor de hele Bijbel.

# Description for a specific level
awards-master-award-level-n-description = Aantal volledig geleerde verzen: { $verse_count ->
    [one]     1 vers
   *[other]   { $verse_count } verzen
 }

# Specific description for level 9
awards-master-award-level-9-description = Heeft heel de Bijbel geleerd!

## 'Verspreider' award.

# Name
awards-sharer-award-name = Verspreider

# General description
awards-sharer-award-general-description =
    Uitgereikt voor het maken van openbaare verzenseries.
    Level 1 is voor het maken van 1 verzenserie, level 5 voor 20 verzenseries.

# Description for a specific level
awards-sharer-award-level-n-description = { $count ->
      [one]    Heeft één openbaare verzenserie gemaakt.
     *[other]  Heeft { $count } openbaare verzenseries gemaakt
  }

## 'Trendsetter' award.

# Name
awards-trend-setter-award-name = Trendsetter

# General description
awards-trend-setter-award-level-general-description =
    Uitgereikt als andere mensen jouw verzenserie gebruiken.
    Level 1 wordt toegekend als minimaal 5 mensen jouw verzenserie leren.

# Description for a specific level
awards-trend-setter-award-level-n-description = Verzenseries gemaakt door deze gebruiker zijn minimaal { $count } keer gebruikt.

## 'Perfectionist' award.

# Name
awards-ace-award-name = Perfectionist

# General description
awards-ace-award-general-description = Uitgereikt als je 100% behaalt bij een test. Level 1 wordt toegekend als je één keer 100% haalt, level 2 als je het twee keer op rij perfect doet, level 3 for 4 keer op rij, level 4 voor 8 keer op rij enzovoorts.

# Description for first level
awards-ace-award-level-1-description = Heeft 100% in een test behaald.

# Description for a specific level.
# $count is the number of times in a row they got 100%,
# will always be greater than 1.
awards-ace-award-level-n-description = Behaalde { $count } keer op rij 100%


## 'Rekruteerder' award.

# Name
awards-recruiter-award-name = Rekruteerder

# General description
# $url is a URL for the referral program help page.
awards-recruiter-award-general-description-html =
   Uitgereikt voor het aanbrengen van nieuwe leden voor LearnScripturen.net via <a href="{ $url }">deze doorverwijzingslink</a>. Level 1 is voor één nieuw lid, en levert 20,000 punten op.

# Description for a specific level 'Recruiter' award.
# $url is a URL for the referral program help page.
# $count is the number of people recruited.
awards-recruiter-award-level-n-description-html = { $count ->
     [one]   Heeft 1 persoon overtuigd om teksten te leren via LearnScripture.net via deze <a href='{ $url }'>link</a>
    *[other] Heeft { $count } personen overtuigd om teksten te leren via LearnScripture.net via deze <a href='{ $url }'>link</a>
 }

## 'Verslaafd' award.

# Name
awards-addict-award-name = Verslaafd

# General description for 'Addict' award
awards-addict-award-general-description = Uitgereikt aan gebruikers die elk uur van de klok een test heeft gedaan.

# Description for 'Addict' award that appears on awardee's page
awards-addict-award-level-all-description = Heeft elk uur van de klok een test gedaan.


## 'Organisator' award.

# Name
awards-organizer-award-name = Organisator

# General description
awards-organizer-award-general-description = Uitgereikt als je mensen samenbrengt in een groep. Level 1 vereist het samenbrengen van minimaal 5 personen in een van je groepen.

# Description for a specific level
awards-organizer-award-level-n-description = Heeft een groep gemaakt die wordt gebruikt door minimaal { $count } personen

## 'Consistente leerling' award.

# Name
awards-consistent-learner-award-name = Consistente leerling

# General description
awards-consistent-learner-award-general-description = Uitgereikt als je voor een langere periode elke dag begint met het leren van minimaal één nieuw vers, zonder onderbrekingen. Let op: je moet verzen wel blijven leren om ze te laten meetellen. Dagen worden gedefinieerd aan de hand van de UTC-tijdzone. Level 1 wordt toegekend bij 1 week, level 10 bij 3 jaar.

# Specific description for level 1
awards-consistent-learner-award-level-1-description =  Is 1 week lang dagelijks gestart met het leren van een nieuw vers
awards-consistent-learner-award-level-2-description = Is 2 weken lang dagelijks gestart met het leren van een nieuw vers
awards-consistent-learner-award-level-3-description = Is 1 maand lang dagelijks gestart met het leren van een nieuw vers
awards-consistent-learner-award-level-4-description = Is 3 maanden lang dagelijks gestart met het leren van een nieuw vers
awards-consistent-learner-award-level-5-description = Is 6 maanden lang dagelijks gestart met het leren van een nieuw vers
awards-consistent-learner-award-level-6-description = Is 9 maanden lang dagelijks gestart met het leren van een nieuw vers
awards-consistent-learner-award-level-7-description = Is 1 jaar lang dagelijks gestart met het leren van een nieuw vers
awards-consistent-learner-award-level-8-description = Is 18 maanden lang dagelijks gestart met het leren van een nieuw vers
awards-consistent-learner-award-level-9-description = Is 2 jaar lang dagelijks gestart met het leren van een nieuw vers
awards-consistent-learner-award-level-10-description = Is 3 jaar lang dagelijks gestart met het leren van een nieuw vers

# Title for award at a specific level.
# $name is award name,
# $level is a number indicating level.
awards-level-title = { $name } - level { $level }

# Caption indicating a specific level award for a specific user
awards-level-awarded-for-user = { $award_name } level { $award_level } trofee voor { $username }
