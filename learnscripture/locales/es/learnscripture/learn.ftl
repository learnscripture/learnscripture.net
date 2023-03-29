
### Learn page:

# Page title
learn-page-title = Memorizar


## Navbar:

# Link that takes the user back to the dashboard
learn-dashboard-link = Panel de control

# Link that takes the user back to where they came from
learn-return-link = Regresar


# This is shown in the top progress bar for a 'review' session.
learn-review-progress-bar-caption = Repaso:

# These are shown in the top bar when data is being saved/loaded
learn-data-working = Transmitiendo…
                   .tooltip = Transmitiendo datos al servidor

# Button that will attempt to re-connect with server after internet
# connection is lost.
learn-reconnect-with-server = Reconectar con el servidor

# Displayed when recording some action failed.
# $item is a description of the action
learn-data-failed = Error - { $item }

# Displayed when some action is in a queue
# $item is a description of the action
learn-data-in-queue = En cola - { $item }


# Displayed when attempting to record an action
# $item is a description of the action
# $attempt is the current attempt number
# $total is the total number of attempts that will be made
learn-data-being-attempted = Intento { NUMBER($attempt) } de { NUMBER($total) } - { $item }

## Navbar - session stats info:

# Displayed before the session stats
learn-session-stats-today = Hoy:

# Tooltip for the 'items started today' stat
learn-items-started-today = Elementos comenzados hoy

# Tooltip for the 'total items tested today' stat
learn-items-tested-today = Elementos probados hoy

## Points menu:

# Displayed as a caption for the points gained in the current learning session
learn-session-points-caption = Puntos de la sesión:

# Tooltip for the points icon
learn-points-icon-caption = Puntos obtenidos durante esta sesión

## Points menu - different reasons for getting points:

learn-initial-test = prueba inicial
learn-review-test = prueba de revisión
learn-revision-completed = revisión completada
learn-perfect-score-bonus = ¡BONUS por puntuación perfecta!
learn-verse-fully-learned-bonus = ¡BONUS por versículo memorizado!
learn-award-bonus = bonus por premio

## Navbar:
# Tooltip for the 'pin/unpin' icon
learn-pin-icon-caption = Anclar/desanclar menú

# Displayed when the current user is not logged in, in place of their username
learn-guest = Invitado

## Loading:

# Displayed when initially loading
learn-loading = Cargando

# Displayed when initially loading, but there is first data to be saved from a previous session
learn-syncing = Sincronizando


## Current verse section:

# Displayed as tooltip for the memory progress percentage value
learn-memory-progress-caption = Progreso de memorización de este versículo


# Displayed as a tooltip for the toggle button that shows the previous verse
learn-toggle-show-previous-verse = Mostrar/ocultar versículo anterior

learn-verse-options-icon-caption = Opciones de versículo


## Instructions section:

learn-read-text-html =
  <b>LEE:</b>
  Lee el texto completo (de preferencia en voz alta), y haz clic en '{ learn-next-button-caption }'.

learn-read-for-context-html =
  <b>LEE:</b>
  Lee este versículo para obtener el contexto y flujo del pasaje.

learn-read-and-recall-html =
  <b>LEE y RECUERDA:</b>
  Lee el texto completo, rellenando los huecos de tu memoria. Haz clic en una palabra para revelarla si no la recuerdas.

# Displayed when the current test is just a practice test
learn-practice-test-note-html =
  <b>PRACTICE</b> test, scores are not counted.
  <b>PRACTICA</b> con un ensayo, la puntuación no se cuenta.

learn-full-word-test-html = <b>PRUEBA:</b> ¡Hora de probar! Escribe el texto, presionando espacio después de cada palabra.

learn-you-dont-need-perfect-spelling = No es neceasaria una ortografía perfecta para obtener puntos.

learn-first-letter-test-html = <b>PRUEBA:</b> ¡Hora de probar! Escribe la <b>primera letra</b> de cada palabra.

learn-choose-from-options-test-html = <b>PRUEBA:</b> ¡Hora de probar! Elige la palabra correcta para cada hueco.

# Test result.
# $score is the accuracy as a percentage.
# $comment is one of the comments below.
learn-test-result-html = <b>RESULTADOS</b> Obtuviste <b>{ NUMBER($score) }</b> - { $comment }

# Comment for better than 98%
learn-test-result-awesome = ¡genial!

# Comment for better than 96%
learn-test-result-excellent = ¡excelente!

# Comment for better than 93%
learn-test-result-very-good = muy bien.

# Comment for better than 85%
learn-test-result-good = bien.

# Comment for less than 85%, or when we are suggesting to try again.
learn-test-result-try-again = ¡inténtalo de nuevo!


# Shows the progress of the verse as a percentage
# $progress is the percentage
# $direction is 'forwards' if they are making progress or 'backwards' if they went back.
# If $direction is 'backwards' then $progress is negative.
learn-verse-progress-result-html =
    <b>PROGRESO:</b>
    { $direction ->
      *[forwards]   +{ NUMBER($progress) } ↗
       [backwards]   { NUMBER($progress) } ↘
    }

learn-verse-progress-complete-html = <b>PROGRESO:</b> ¡Llegaste al 100% - bien hecho!

## Action choices:

learn-next-button-caption = Siguiente

learn-back-button-caption = Atrás

# Indicates a verse is fully learned
learn-verse-fully-learned = Memorizado por completo


# Displayed under 'practice' button, to indicate it will happen right now.
learn-see-again-now = Ahora


# Displayed when a verse will be seen again in less than 1 hour
learn-see-again-less-than-an-hour = < 1 hora

# Displayed when a verse will be seen again after between 1 and 24 hours.
# $hours is the number of hours
learn-see-again-hours = { $hours ->
                           [one]    una hora
                          *[other]  { $hours } horas
                        }

# Displayed when a verse will be seen again after between 1 and 7 days
# $days is the number of days
learn-see-again-days = { $days ->
                           [one]    un día
                          *[other]  { $days } días
                        }

# $weeks is the number of weeks
learn-see-again-weeks = { $weeks ->
                           [one]    una semana
                          *[other]  { $weeks } semanas
                        }

# Displayed when a verse will be seen again after several months
# $months is the number of months
learn-see-again-months = { $months ->
                           [one]    un mes
                          *[other]  { $months } meses
                        }

## Verse options menu:

learn-skip-this-verse = Saltar este versículo por ahora

learn-skip-this-question = Saltar esta pregunta por ahora

learn-stop-learning-this-verse = Dejar de memorizar este versículo

learn-stop-learning-this-question = Dejar de memorizar esta pregunta

learn-reset-progress = Reiniciar progreso

learn-test-instead-of-read = Hacer pruebas en lugar de leer

## Buttons under verse:

# Button for getting a hint.
# $used is the number of hints used so far,
# $total is the number of hints available,
# so it looks like "Use hint (1/2)"
learn-hint-button = Usar pista ({ NUMBER($used) }/{ NUMBER($total) })

# Button used to accept and go to next verse
learn-next-button = Aceptar

# Button used to choose to practice a verse
learn-practice = Practicar

# Button used to practice a verse for a second/third time.
learn-practice-again = Practicar de nuevo

# Button used to choose to see a verse sooner that normal schedule
learn-see-sooner = Ver más seguido

## Help section:

# Link that toggles the help section to be visible
learn-help = Ayuda
           .tooltip = Mostrar/ocultar ayuda

learn-take-the-help-tour = Tomar el tour de ayuda.

learn-you-can-finish =
  Puedes terminar tu repaso o sesión de memorización en cualquier momento
  usando el botón Regresar en la esquina superior izquierda.

learn-keyboard-navigation-help =
  Navegación con teclado (para teclados físicos, no para pantallas táctiles):
  utiliza Tab y Shift-Tab para mover enfocar diferentes controles y Enter para presionarlos.
  El control enfocado se muestra con un borde de color.

learn-button-general-help =
  El botón para la acción más probable está resaltado en color y está enfocado por defecto.

# The '<a>' and '</a>' wrap the text that will become a hyperlink to change preferences
learn-you-can-change-your-testing-method-html =
    Puedes cambiar tu método de prueba en cualquier momento en tus <a>preferencias</a>.

# The '<a>' and '</a>' wrap the text that will become a hyperlink to change preferences
learn-on-screen-testing-not-available-html =
    El método de prueba en pantalla no está disponible para este versículo en esta versión.
    ¡Lo sentimos! Por favor elige otra opción en tus <a>preferencias</a>.


## Help tour:

# Button to finish the tour (at any point)
learn-help-tour-exit = Salir del tour

# Button to go to previous step in help tour
learn-help-tour-previous = Anterior

# Button to go to next step in help tour
learn-help-tour-next = Siguiente

# Button that closes the help tour at the end
learn-help-tour-finish = Finalizar

# First message shown in help tour
learn-help-tour-hello =
    ¡Hola! Este tour guiado te llevará por la interfaz de la página de memorización.

learn-help-tour-dashboard-link =
    Usa el enlace en la esquina superior izquierda para volver al panel de control en cualquier momento.

learn-help-tour-progress-bar =
    Esta barra muestra tu progreso en memorizar un versículo por primera vez, o tu progreso total en una sesión de repaso.

learn-help-tour-total-points =
    El total de puntos que has ganado en el lote actual de versículos se muestra aquí.

learn-help-tour-create-account =
    Debes crear una cuenta (desde el enlace en tu panel de control) para empezar a ganar puntos.

learn-help-tour-open-menu =
    Presiona en este encabezado para mostrar más detalles.

learn-help-tour-pin-menu =
    También puedes anclar este menú a un lado (pantallas grandes) o arriba (pantallas pequeñas) para que sea visible siempre.

learn-help-tour-close-menu =
    Presiona el encabezado de nuevo para cerrarlo.

learn-help-tour-problem-saving-data =
    Si hay algún problema guardando tus datos, se mostrará aquí. Presiona el encabezado del menú para más información.


learn-help-tour-internet-connection-cut =
    Si tu conexión a internet se corta completamente, no te preocupes - puedes seguir trabajando y luego intentar guardar tus datos de nuevo cuando tu conexión se restablezca.

learn-help-tour-new-verses =
    Este es el número de versículos nuevos que has empezado hoy. Si eres nuevo en LearnScripture, es importante ir a tu propio ritmo. Recomendamos memorizar un versículo nuevo cada día.

learn-help-tour-tested-verses =
    Este es el número de versículos para los que has hecho pruebas hoy.

learn-help-tour-preferences =
    Puedes cambiar tus preferencias en cualquier momento desde aquí.

learn-help-tour-verse-progress =
    El progreso aproximado de cada versículo que estás memorizando se muestra aquí.

learn-help-tour-verse-options =
    Este menú muestra opciones adicionales para el versículo actual.

learn-help-tour-finish-test =
    Cuando hayas terminado una prueba, tu puntuación se usa para estimar tu progreso en el versículo y programar el siguiente repaso. Debajo de cada botón hay un texto indicando aproximadamente cuándo volverás a ver el versículo si eliges esa opción.

learn-help-tour-end =
    Eso es todo por ahora - ¡gracias por tomar el tour! Puedes tomarlo de nuevo en cualquier momento (en la sección 'Ayuda').

## Confirmation messages:

learn-confirm-leave-page-failed-saved =
   Algunos datos no se pudieron guardar. Si sales de esta página, se perderán los datos. ¿Quieres salir?

learn-confirm-leave-page-save-in-progress =
   Los datos todavía se están guardando. Si sales de esta página, se perderán los datos. ¿Quieres salir?

learn-confirm-reset-progress =
   Estas a punto de reiniciar tu progreso en este elemento a cero. ¿Estás seguro?

## Saving data - descriptions of different data items being saved:

# Marking an item as done. $ref is a verse reference (or catechism reference)
learn-save-data-item-done = Marcando como completado - { $ref }

# Saving score for item. $ref is a verse reference (or catechism reference)
learn-save-data-saving-score = Guardando puntuación - { $ref }

# Recording that item was read. $ref is a verse reference (or catechism reference)
learn-save-data-read-complete = Registrando lectura - { $ref }

# Recording that item was skipped. $ref is a verse reference (or catechism reference)
learn-save-data-recording-skip = Registrando salto - { $ref }

# Recording that an item was cancelled. $ref is a verse reference (or catechism reference)
learn-save-data-recording-cancel = Registrando cancelación - { $ref }

# Recording that progress was reset for an item. $ref is a verse reference (or catechism reference)
learn-save-data-recording-reset-progress = Reiniciando progreso de { $ref }

# Recording that an item was marked for being reviewed sooner. $ref is a verse reference (or catechism reference)
learn-save-data-marking-review-sooner = Marcando { $ref } para repasar más temprano

# Loading verses etc.
learn-loading-data = Cargando elementos para memorizar...


## Error messages

# Error that normally appears only if there is an internet connection problem.
# $errorMessage gives a more specific error message.
learn-items-could-not-be-loaded-error =
    Ocurrió un error al cargar (mensaje de error: { $errorMessage }). Comprueba tu conexión a internet.
