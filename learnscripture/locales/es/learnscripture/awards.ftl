## Awards/badges.

# Notification received when a user gets a new award/badge,
# $award is the award name (appears as a link)
awards-new-award-html = Obtuviste una nueva insignia: { $award }.

# Notification received when a user gets a higher level for an award/badge
# $award is the award name (appears as a link)
awards-levelled-up-html = Haz subido de nivel en una de tus insignias: { $award }.

# Notification when there are points for an award that has been received.
# $points is the number of points given
awards-points-bonus =  Puntos bonificados: { $points }.

# Appears next to notification about new award, as shortcuts for
# telling other people about the award.
# $twitter is a link to Twitter.
awards-tell-people-html = Compartir: { $twitter }

# Default message that is used for sharing about awards on social media
# $award is the award name/description
awards-social-media-default-message = He ganado una insignia: { $award }

## Awards page.

# Page title
awards-page-title = Insignias

awards-the-following-are-available = Estas insignias están disponibles:


# Caption in table header for award name/icon
awards-award = Insignia

# Caption in table header for when the award was received
awards-date-received = Fecha

# Caption in table header for award icon
awards-icon = Icono

# Caption in table header for award description
awards-description = Descripción

# Caption in the table header for award points
awards-points = Puntos

# Indicates the level of an award/badge
awards-award-level = nivel { $level }

# Indicates the highest level that has so been achieved for the award
award-highest-level-achieved-html = Nivel más alto alcanzado: <b>nivel { $level }</b>

# Link to page showing details about who has achieved the award,
# $name is the name/short description of the award
award-people-with-award = Personas con la insignia { $name }



## Individual award page.

# Page title,
# $name is the award name/short description
awards-award-page-title = Insignia - { $name }

# Heading for description of award
awards-description-subtitle = Descripción

# Heading for list of people who have achieved the award
awards-achievers-subtitle = Ganadores

# Indicates the highest level that can be achieved for an award
awards-award-highest-level = El nivel { $level } es el nivel más alto.

# Subtitle
awards-level-subtitle = Nivel { $level }

# Indicates the number of people who have achieved the award at this level, followed
# by a list containing all those users
awards-level-achievers-all = Total { $count ->
    [one]    un usuario
   *[other]  { $count } usuarios
 }:

# Indicates the number of people who have achieved the award at this level, followed
# by a list containing a sample of those users.
awards-level-achievers-truncated = Total { $count ->
    [one]    un usuario
   *[other]  { $count } usuarios
 }, incluyendo:


# Link to page showing all badges
awards-all-available-badges = Todas las insiginas disponibles

# Link to page showing user's badges
awards-your-badges = Tus insignias

# Subtitle for section describing the user's level for the award being described
awards-your-level = Tu nivel

# Used when the award has levels, and the user has the award at a certain level
awards-you-have-this-award-at-level = Tienes esta insignia en el nivel { $level }.

# Used when the award has does not have levels, and the user has the award.
awards-you-have-this-award = Tienes esta insignia.

# Used when the user doesn't have the award
awards-you-dont-have-this-award = Aun no tienes esta insignia.

# Message used when trying to view some old awards
awards-removed = La insignia ‘{ $name }’ ya no está en uso

## 'Student' award.

# Name
awards-student-award-name = Estudiante

# General description
awards-student-award-general-description = Otorgada por empezar a memorizar versículos. El nivel 1 es por un versículo, y llega hasta el nivel 9 por toda la Biblia.

# Description for a specific level
awards-student-award-level-n-description = Memorizar por lo menos { $verse_count ->
    [one]    un versículo
   *[other]  { $verse_count } versículos
 }

# Specific description for level 9
awards-student-award-level-9-description = ¡Memorizar toda la Biblia!

## 'Master' award.

# Name
awards-master-award-name = Maestro

# General description
awards-master-award-general-description =
   Otorgada por memorizar versículos completamente (5 estrellas). Esto toma
   alrededor de un año para asegurarse que has memorizado los versículos
   permanentemente. El nivel 1 es por un versículo, y llega hasta el nivel 9 por
   toda la Biblia.

# Description for a specific level
awards-master-award-level-n-description = Finalizar de memorizar { $verse_count ->
    [one]     un versículo
   *[other]   { $verse_count } versículos
 }

# Specific description for level 9
awards-master-award-level-9-description = ¡Finalizar de memorizar toda la Biblia!

## 'Sharer' award.

# Name
awards-sharer-award-name = Generoso

# General description
awards-sharer-award-general-description =
    Otorgada por crear conjuntos públicos de versículos (selecciones).
    El nivel 1 es por un conjunto, hasta el nivel 5 por 20 conjuntos.

# Description for a specific level
awards-sharer-award-level-n-description = { $count ->
      [one]    Crear un conjunto público de versículos
     *[other]  Crear { $count } conjuntos públicos de versículos
  }


## 'Trend Setter' award.

# Name
awards-trend-setter-award-name = Marca tendencias

# General description
awards-trend-setter-award-level-general-description =
    Otorgado por crear conjuntos de versículos que otros utilizan.
    El nivel 1 es por cinco personas que utilizan uno de tus conjuntos.

# Description for a specific level
awards-trend-setter-award-level-n-description = Los conjuntos de versículos creados por este usuario han sido usados por otros al menos { $count } veces.


## 'Ace' award.

# Name
awards-ace-award-name = Perfeccionista

# General description
awards-ace-award-general-description =
    Otorgado por obtener 100% en una prueba. El nivel 1 es por obtener 100% una
    vez, el nivel 2 por dos veces seguidas, el nivel 3 por cuatro veces, el
    nivel 4 por ocho veces, etc.
# Description for first level
awards-ace-award-level-1-description = Obtener 100% en una prueba

# Description for a specific level.
# $count is the number of times in a row they got 100%,
# will always be greater than 1.
awards-ace-award-level-n-description = Obtener 100% en una prueba { $count } veces seguidas


## 'Recruiter' award.

# Name
awards-recruiter-award-name = Reclutador

# General description
# $url is a URL for the referral program help page.
awards-recruiter-award-general-description-html =
   Otorgado por conseguir que otros se unan utilizando nuestro <a href="{ $url
   }">programa de referidos</a>. El nivel 1 es por una referencia, y vale por
   20,000 puntos.

# Description for a specific level 'Recruiter' award.
# $url is a URL for the referral program help page.
# $count is the number of people recruited.
awards-recruiter-award-level-n-description-html = { $count ->
    [one]   Conseguir que una persona se una a LearnScripture.net usando el <a href='{ $url }'>programa de referidos</a>
    *[other] Conseguir que { $count } personas se unan a LearnScripture.net usando el <a href='{ $url }'>programa de referidos</a>
 }

## 'Addict' award.

# Name
awards-addict-award-name = Adicto

# General description for 'Addict' award
awards-addict-award-general-description = Otorgado por hacer pruebas de versículos durante todas las horas del reloj.

# Description for 'Addict' award that appears on awardee's page
awards-addict-award-level-all-description = Completar pruebas de versículos durante todas las horas


## 'Organizer' award.

# Name
awards-organizer-award-name = Organizador

# General description
awards-organizer-award-general-description = Otorgado por reunir a otros en grupos. El nivel 1 requiere que cinco personas se unan a uno de tus grupos.

# Description for a specific level
awards-organizer-award-level-n-description = Crear grupos utilizados por al menos { $count } personas

## 'Consistent learner' award.

# Name
awards-consistent-learner-award-name = Estudiante consistente

# General description
awards-consistent-learner-award-general-description =
    Otorgado por empezar a memorizar nuevos versículos durante un período de
    tiempo sin falta. Debes memorizar los versículos constatemente para que
    cuenten. Los días se definen de acuerdo a la zona horaria UTC. El nivel 1 es
    por 1 semana, el 10 por tres años.

# Specific description for level 1
awards-consistent-learner-award-level-1-description = Empezar a memorizar un nuevo versículo todos los días por una semana
awards-consistent-learner-award-level-2-description = Empezar a memorizar un nuevo versículo todos los días por dos semanas
awards-consistent-learner-award-level-3-description = Empezar a memorizar un nuevo versículo todos los días por un mes
awards-consistent-learner-award-level-4-description = Empezar a memorizar un nuevo versículo todos los días por tres meses
awards-consistent-learner-award-level-5-description = Empezar a memorizar un nuevo versículo todos los días por seis meses
awards-consistent-learner-award-level-6-description = Empezar a memorizar un nuevo versículo todos los días por nueve meses
awards-consistent-learner-award-level-7-description = Empezar a memorizar un nuevo versículo todos los días por un año
awards-consistent-learner-award-level-8-description = Empezar a memorizar un nuevo versículo todos los días por 18 meses
awards-consistent-learner-award-level-9-description = Empezar a memorizar un nuevo versículo todos los días por dos años
awards-consistent-learner-award-level-10-description = Empezar a memorizar un nuevo versículo todos los días por tres años

# Title for award at a specific level.
# $name is award name,
# $level is a number indicating level.
awards-level-title = { $name } - nivel { $level }

# Caption indicating a specific level award for a specific user
awards-level-awarded-for-user = { $award_name } nivel { $award_level } otorgado a { $username }
