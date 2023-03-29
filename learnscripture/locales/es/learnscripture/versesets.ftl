## Verse sets.

# Caption for the 'name' field of a verse set
versesets-name = Nombre

# Caption for the 'description' field of verse sets
versesets-description = Descripción

# Caption for the 'additional info' field of verse sets
versesets-additional-info = Información adicional

# Caption for the 'public' field when creating a Verse Set
versesets-public = Hacer público (no se puede deshacer)

# Caption for the 'language' field of verse sets.
versesets-language = Idioma
                   .help-text = El idioma usado en los campos ‘{ versesets-name }’, ‘{ versesets-description}’ y ‘{ versesets-additional-info }’.

## Searching and filtering verse sets.

# Caption for the search input box for searching for verse sets
versesets-search = Buscar

# Caption for the filter to select type of verse set (selection or passage)
versesets-filter-type = Tipo

# Caption for filtering by 'Selection' verse sets
versesets-filter-selection-caption = Selección - versículos seleccionados a mano, generalmente sobre un solo tema

# Caption for filtering by 'Passage' verse sets
versesets-filter-passage-caption = Pasaje - versículos continuos en un capítulo

# Caption for showing all verse set types (selection and passage)
versesets-filter-all = Todos

# Caption for the sorting options of the verse sets
versesets-order = Orden

# Caption for ordering verse sets by most popular first
versesets-order-most-popular-first = Más popular primero

# Caption for ordering verse sets by newest first
versesets-order-newest-first = Más reciente primero



## Viewing a verse set.

# Page title.
# $name is the name of the verse set being viewed.
versesets-view-set-page-title = Conjunto de versículos: { $name }

# Sub-title for list of verses in set
versesets-view-set-verses-title = Versículos

# Message displayed when verse set is empty
versesets-view-set-no-verses = ¡No hay versículos en este conjunto!



# Sub-title for additional notes about the verse set
versesets-view-set-notes-title = Notas

# Note about how to opt out of learning
versesets-view-set-how-to-opt-out =
    Al memorizar un conjunto, puedes optar por no memorizar un versículo en particular presionando
    ‘{ learn-stop-learning-this-verse }’ en la página de memorización.

# Note about verse set being public
versesets-view-set-learning-is-public =
    memorizar un conjunto de versículos es una acción pública
    (a menos que el conjunto sea privado y permanezca privado)

# Prompt to change a verse set to a 'passage set'
versesets-view-set-change-to-passage-set =
    Parece que has seleccionado un conjunto de versículos continuos. Recomendamos que uses
    un conjunto tipo 'pasaje' en lugar de uno tipo 'selección'. Puedes convertirlo usando
    el botón a continuación:

# Button to change to passage set
versesets-view-set-change-to-passage-set-button = Convertir a pasaje


# Notice displayed when a 'selection' verse set is converted to a 'passage' verse set
versesets-converted-to-passage = Conjunto convertido a tipo pasaje

# Button to edit the verse set being displayed
versesets-view-set-edit-button = Editar

# Sub-title for section with additional info about the verse set
versesets-view-set-info-title = Información del conjunto

# Indicates who put the verse set together.
versesets-view-set-put-together-by-html = Recopilado por { $username }

# Indicates when the verse set was created
versesets-view-set-date-created = Creado el { DATETIME($date_created) }.

# Shown when the verse set is private
versesets-view-set-private = Privado - este conjunto sólo es visible para ti.

# Sub-title for section about the user's use of this verse set
versesets-view-set-status-title = Estado

# Shown when the user isn't learning the verse set at all (in the given Bible version).
# $version_name is the name of a Bible version.
versesets-view-set-not-learning = Todavía no has memorizado este conjunto en { $version_name }.

# Shown when the user has started learning all the verses in the verse set.
# $version_name is the name of a Bible version.
versesets-view-set-learning-all = Has comenzaado a memorizar los versículos de este conjunto en { $version_name }.

# Shown when the user has started learning some of the verses in the verse set.
# $started_count is the number they have started learning.
# $total_count is the total number of verses in the set.
# $version_name is the name of a Bible version.
versesets-view-set-learning-some = Has comenzado a memorizar { $started_count } de { $total_count } versículos de este conjunto en { $version_name }.

# Shown when the user has some verses in this set in their learning queue.
# $in_queue_count is the number of verses in their queue.
# $version_name is the name of a Bible version.
versesets-view-set-number-in-queue =
  Tienes { $in_queue_count ->
     [one]      un versículo
    *[other]    { $in_queue_count } versículos
  } de este conjunto en tu cola de memorización en la versión { $version_name }.

# Beginning of section regarding removing verses from learning queue
versesets-view-set-remove-from-queue-start = Si quieres eliminarlos:

# First method for removing verses from queue
versesets-view-set-remove-from-queue-method-1 =
    elimínalos individualmente desde la interfaz de memorización presionando
    ‘{ learn-stop-learning-this-verse }’
    en el menú de opciones del versículo cuando aparezca para memorizar.

# Second method for removing verses from queue, followed by a button to remove all
versesets-view-set-remove-from-queue-method-2 = O puedes eliminarlos a todos:

# Button to drop all verses from queue
versesets-view-set-drop-from-queue-button = Eliminar de la cola

# Noticed displayed after the user chooses to remove some verses from their learning queue
versesets-dropped-verses =
    Se { $count ->
      [one]   eliminó un versículo
      *[other] eliminaron { $count } versículos
    } de tu cola de memorización.


## Creating/editing verse sets.

# Page title for editing
versesets-edit-set-page-title = Editar conjunto de versículos

# Page title for creating a selection set
versesets-create-selection-page-title = Crear conjunto de selección

# Page title for creating a passage set
versesets-create-passage-page-title = Crear conjunto de pasaje

# Sub title when editing verse sets, for title/description fields
versesets-about-set-fields = Acerca del conjunto

# Sub title when editing verse sets, for list of verses in set
versesets-verse-list = Lista de versículos

# Message displayed in verses when no verses have been added yet
versesets-no-verses-yet = ¡No se ha añadido ningún versículo!

# Validation error message if user tries to create set with no verses
versesets-no-verses-error = No hay versículos en el conjunto.

# Success message when a verse set is saved
versesets-set-saved = El conjunto '{ $name }' se ha guardado.

# Sub title for the section with controls for adding verses
versesets-add-verses-subtitle = Añadir versículos

# Caption on button for adding a verse to a verse set
versesets-add-verse-to-set = Añadir al conjunto

# Caption for the button that saves the edited/new verse set
versesets-save-verseset-button = Guardar conjunto

# Sub title for section that allows you to choose a passage
versesets-choose-passage = Escoger pasaje

versesets-natural-break-explanation =
  Para pasajes de más de 10 versículos, es útil que indiques los
  saltos naturales en el pasaje marcando la casilla 'Salto de sección' en los versículos
  que comienzan una nueva sección o párrafo.

# Explanation of 'breaks'
versesets-natural-break-explanation-part-2-html =
  <b>NOTA:</b> los saltos de sección son <b>adicionales</b> a los saltos de
  versículo para indicar secciones <b>más grandes</b>. Al memorizar, sólo se te
  presentará un versículo a la vez, incluso si no añades saltos de sección.

# Heading for section break column
versesets-section-break = Salto de sección

# Sub title for section with optional fields
versesets-optional-info = Información adicional opcional

# Shown when the user enters a passage reference and there are other verse sets for that passage
versesets-create-duplicate-passage-warning = Ya existen algunos conjuntos de versículos para este pasaje.

## Viewing user's own verse sets.

# Sub-title for section showing the list of verse sets the user is learning
versesets-you-are-learning-title = Conjuntos que estás memorizando

# Sub-title for section showing the list of verse sets the user created
versesets-you-created-title = Conjuntos creados por ti
