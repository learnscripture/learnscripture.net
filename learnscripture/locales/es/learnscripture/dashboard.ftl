### Dashboard page
# Title of 'dashboard' page
dashboard-page-title = Panel de control

# Notice that appears for guest users who haven't created an account yet
dashboard-remember-to-create-an-account-html =
    <b>Recuerda <a href="{ $signup_url }">crear una cuenta</a></b> - ¡de lo
    contrario tu progreso se perderá! Es gratis, solo toma unos segundos y te
    permite muchas características adicionales como insignias, grupos, tablas
    de clasificación y páginas de estadísticas. Como invitado, tus datos
    caducarán el { DATETIME($expires) }.


## Unfinished session section.

# Sub title
dashboard-continue-title = Continuar

dashboard-unfinished-notice = Tienes una sesión sin terminar.

dashboard-unfinished-notice-part-2 = Continuar la sesión para sincronizar los datos.

# Caption for button that will continue the session
dashboard-continue-button = Continuar

## Heatmap section.

dashboard-learning-events = Eventos de memorización

## Review section.

# Sub title
dashboard-review-title = Repaso

# Button for reviewing a whole passage
dashboard-review-whole-passage-button = Todo el pasaje

# Button for reviewing one section of a passage.
# $verse_count is the number of verses in that section.
dashboard-review-one-section-button = Una parte ({ $verse_count } vss)

# Button for reviewing a verse or set of verses, or a catechism question
dashboard-review-button = Repasar

# Button for cancelling learning a verse/passage
dashboard-cancel-learning = Cancelar

# Note shown when the whole passage is due for review
# $verse_count is the number of verses in the passage
dashboard-passage-due-for-review = Este pasaje está listo para repasar ({ $verse_count } vss).

# Note shown when part of a passage verse set is due for review.
# $needs_testing_count is the number that are due for review,
# $total_verse_count is the total number of verses in the passage
dashboard-passage-part-due-for-review = { $needs_testing_count } de { $total_verse_count } versículos están listos para repasar.

# Indicates the number of verses due for review (separate from the passage verse sets)
dashboard-verses-for-review-count =
  Actualmente tienes { $count ->
    [one]     1 versículo
   *[other]  { $count } versículos
  } listos para repasar.

# Displayed before a list of verse references that are due for review or learning
dashboard-verses-coming-up = Versículos que vienen:

# Indicates the number of catechism questions due for review
dashboard-catechism-questions-for-review-count = Tienes { $count } pregunta(s) listas para repasar.

# Message shown if there is nothing in the general queue due for reviewing. (Excludes passage verse sets)
dashboard-general-queue-empty = No tienes nada listo para repasar.

# Message about the next verse due for review.
# $title is the verse reference or catechism title,
# $timeuntil is a string like "5 minutes" or "3 hours"
dashboard-next-item-due-html = <b>{ $title }</b> estará listo para repasar en { $timeuntil }.


## Learn section.

# Sub title
dashboard-learn-title = Memorizar

# Button to start learning a passage
dashboard-learn-start-learning-button = Empezar a memorizar

# Button to continue learning a passage (they have already started at least one verse)
dashboard-learn-continue-learning-button = Continuar memorizando

# Message displayed for a passage set that is in the user's queue
# for learning (but that haven't started yet)
dashboard-passage-queued = Este pasaje está en tu cola para memorizar.

# Message on a passage verse set indicating the number of items learned
# and still not started.
dashboard-passages-youve-seen-verses =
     Haz visto { $tested_total ->
        [1]     1 versículo
        *[other] { $tested_total } versículos
     } hasta ahora, faltan { $untested_total } por empezar.

# Message on a passage verse set indicating the number of items learned
# and still not started, inluding info about those that are due for review.
dashboard-passages-youve-seen-verses-with-review-due-html =
    Haz visto { $tested_total ->
        [1]     1 versículo
        *[other] { $tested_total } versículos
    } hasta ahora, <b>hay { $needs_review_total } listos para repasar</b>,
    faltan { $untested_total } por empezar.


# Sub title for verses that aren't part of a verse set
dashboard-learn-other-verses = Otros versículos

# Shows number of verses in queue for learning
dashboard-queued-verses = Versículos en cola para memorizar: { $count }

# Shows number of verses in a particular set in queue for learning
dashboard-queued-verses-in-set = Haz añadido { $count } versículos nuevos a la cola para memorizar en este conjunto.

# Button to learn a verse or queue of verses
dashboard-learn-button = Memorizar

# Button to remove items from the queue of verses to learn
dashboard-clear-queue-button = Limpiar cola

# Indicates the total number of questions in a catechism that has been queued for learning
dashboard-catechism-question-count = Haz añadido este catecismo a la cola, { $count } preguntas en total.

# Indicates the number of questions in a catechism that have been started, and how many remain.
dashboard-catechism-learned-and-remanining-count =
   Has visto { $started_count ->
       [one]     1 pregunta
      *[other]   { $started_count } preguntas
   } hasta ahora, faltan { $remaining_count }.

# Message displayed when there are no passages, verses or catechisms queued for learning
dashboard-learn-nothing-in-queue = La cola está vacía.

# Confirmation prompt after clicking 'clear queue' button for verses
dashboard-remove-verses-from-queue-confirm =
    Estás a punto de borrar los versículos seleccionados de tu cola para
    memorizar. Para memorizarlos tendrás que seleccionarlos de nuevo. ¿Quieres
    continuar?

# Confirmation prompt after clicking 'cancel' button for a catechism
dashboard-remove-catechism-from-queue =
    Estás a punto de borrar las preguntas seleccionadas de tu cola para
    memorizar. Para memorizarlas tendrás que seleccionarlas de nuevo. ¿Quieres
    continuar?

# Confirmation prompt after clicking 'cancel' for a passage verse set
dashboard-cancel-passage-confirm =
    Estas a punto de cancelar la memorización de este pasaje en esta versión. Los
    resultados de las pruebas se guardarán. ¿Quieres continuar?


## 'Choose' section.

# Sub title
dashboard-choose-title = Elegir

dashboard-choose-link-html = Cuando hayas terminado con lo de arriba, <a href="{ $url }">elige algunos versículos o un pasaje para memorizar.</a>

## Right column.

dashboard-todays-stats-title = Estadísticas de hoy

# Indicates the number of new verses the user has started today
dashboard-todays-stats-new-verses-begun = Versículos nuevos empezados: { $new_verses_begun }

# Indicates the number of verses the user has been tested on today
dashboard-todays-stats-total-verses-tested = Versículos probados: { $total_verses_tested }

# Sub title for the list of groups the user is a member of
dashboard-your-groups-title = Tus grupos

# Link to see all groups the user is a member of, appears at bottom of a truncated list
dashboard-groups-see-all = (ver todos)

dashboard-view-other-groups-link = Ver otros grupos

dashboard-why-not-join-a-group-html = No estás en ningún grupo todavía. ¿Quieres <a href="{ $url }">unirte a uno?</a>

## News section.

# Sub title
dashboard-news-title = Noticias

# Link to the news page
dashboard-more-news-link = Ver más noticias...
