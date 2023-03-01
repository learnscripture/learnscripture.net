### User accounts related text.

## Account information.

# Caption for username field
accounts-username = Nombre de usuario

# Caption for first name field, editable on account details page
accounts-first-name = Primer nombre

# Caption for last name field, editable on account details page
accounts-last-name = Apellido


# Caption for full name field (combined first name and last name)
accounts-full-name = Nombre

# Caption for email field
accounts-email = Correo electrónico

# Caption for password field
accounts-password = Contraseña

# Caption for date the user joined the website
accounts-date-joined = Fecha de alta

# Caption for "user is under 13 years old" field
accounts-under-13 = Menor de 13 años

# Caption for user field that enables the comment system (true/false)
accounts-enable-commenting = Habilitar sistema de comentarios

# Caption for 'account' field
accounts-account = Cuenta

# Caption for the Account 'date created' field
accounts-date-created = Fecha de creación

## Account details page.

# Page title
accounts-details-page-title = Detalles de la cuenta

# Sub title
accounts-details-personal-info-subtitle = Información personal

# Sub title indicating data that won't be publicly visible
accounts-details-private-info-subtitle = Privada

# Sub title indicating data that will be publicly visible
accounts-details-public-info-subtitle = Pública

# Success message when details are updated
accounts-details-updated = La cuenta ha sido actualizada, gracias


## Preferences.

# Page title
accounts-preferences-title = Preferencias

# Shown at top of preferences page
accounts-preferences-instructions = Configura tus preferencias y presiona '{ accounts-preferences-save-button }' para continuar.

# Additional notes about preferences
accounts-preferences-instructions-additional-notes =
    Todas las preferencias pueden ajustarse más tarde, y la
    versión de la Biblia puede elegirse para cada versículo


# Caption for the account 'default bible version' field
accounts-default-bible-version = Versión de la Biblia predeterminada

# Caption for choice of testing method (how verses are tested)
accounts-testing-method = Método de prueba

accounts-type-whole-word-testing-method = Escribir la palabra - más completo

accounts-type-first-letter-testing-method = Escribir la primera letra - más rápido

accounts-choose-from-list-testing-method = Elegir la palabra de la lista - ideal para dispositivos móviles.

accounts-desktop-testing-method = Método de prueba para escritorio

accounts-touchscreen-testing-method = Método de prueba para pantalla táctil


# Caption for 'enable animations' field
accounts-enable-animations = Habilitar animaciones

# Caption for 'enable sounds' field
accounts-enable-sounds = Habilitar sonidos

# Caption for 'enable vibration' field
accounts-enable-vibration = Vibrar al equivocarse
                          .help-text = Depende de las capacidades del dispositivo


# Caption for choice of interface colour theme
accounts-interface-theme = Apariencia

# Name of interface theme that is a slate blue colour
accounts-slate-theme = Pizarrón

# Name of interface theme that is a neon pink
accounts-bubblegum-pink-theme = Dulce rosa

# Name of interface theme that is a neon green
accounts-bubblegum-green-theme = Dulce verde

# Name of interface theme that is dark with 'Space' colours
accounts-space-theme = Espacio

# Caption for 'interface language' field
accounts-interface-language = Idioma de la interfaz

# Caption for button to save changes to preferences
accounts-preferences-save-button = Guardar

# Caption for button to cancel changes and close preferences dialog
accounts-preferences-cancel-button = Cancelar

## Account notifications.

# Notification when user is invited to join a group,
# $user is the person who invited them,
# $group is the name of the group
accounts-invitation-received-html = { $user } te ha invitado a unirte al grupo { $group }


## Signup.

# Title of 'create account'/'signup' page
accounts-signup-title = Crear cuenta

# Message displayed if the user goes to the sign up page but is already logged in.
accounts-already-logged-in-html = Ya iniciaste sesión como <b>{ $username }</b>. Deberás <a href="#" class="logout-link">cerrar sesión</a> si quieres crear una nueva cuenta.

accounts-signup-agree-to-terms-of-service-html =
        Al crear una cuenta aceptas nuestros
        <a href="/terms-of-service/" target="_blank">términos de servicio</a> y
        <a href="/privacy-policy/" target="_blank">política de privacidad</a>.
        Ten en cuenta que los niños menores de 13 años no pueden crear una
        cuenta, pero su padre o encargado puede hacerlo por ellos y debe marcar
        la casilla correspondiente que aparece arriba.

accounts-signup-parents-notice =
        Los padres o encargados que no quieren que sus hijos tengan contacto con
        otros usuarios a través del sistema de comentarios pueden deshabilitar
        la opción de comentar desmarcando la casilla que aparece arriba.

# Button to create account after filling in form
accounts-signup-create-account-button = Crear cuenta


# Message displayed if user tries to put invalid characters in their chosen username
accounts-username-validation = Sólo se permiten letras, números y estos símbolos: . + - _

# Message displayed if password is too short
accounts-password-length-validation = La contraseña debe tener al menos { $length } caracteres

# Message displayed if user tries to choose a username that is already taken
accounts-username-already-taken = Este nombre de usuario ya está en uso

# Help text for email field when signing up
accounts-email-help-text = Confidencial. Utilizado sólo para restablecer la contraseña.

# Notification when a user signs up
accounts-signup-welcome-notice = Cuenta creada - bienvenido/a { $username }!


## Login.

# Title of log-in page
accounts-login-title = Inicio de sesión

# Caption for the email/username input box
accounts-login-email-or-username = Correo electrónico o nombre de usuario

# Message shown when the user enters a wrong username, email or password
accounts-login-no-matching-username-password = No se encontró ninguna cuenta con ese correo/nombre y contraseña

# Message shown when the user enters an email address to log in, but multiple accounts exist for that email address
accounts-login-multiple-accounts = Existen múltiples cuentas con esta dirección de correo. Utiliza el nombre de usuario

# Message shown when the user tries to reset their password, but enters an email address that isn't found
accounts-reset-email-not-found = No se econtró ninguna cuenta asociada a esta dirección. ¿Estás seguro que existe la cuenta?

# Shown when trying to change or set password and the passwords don't match
accounts-password-mismatch = Los campos de contraseña no coinciden.

## Password reset.

# Page title for start page
accounts-password-reset-start-page-title = Restablecimiento de contraseña

accounts-password-reset-start-email-sent =
    Hemos enviado instrucciones para restablecer la contraseña a tu cuenta de
    correo electrónico. Llegarán pronto.

# Page title for main reset page
accounts-password-reset-page-title = Restablecimiento de contraseña

# Instructions at top of password reset new password form
accounts-password-reset-new-password-instructions =
    Introduce la nueva contraseña dos veces para verificar que fue escrita correctamente


# Title password reset was unsuccessful
accounts-password-reset-unsuccessful-title = Falló de restablecimiento de contraseña

# Message shown when password reset was unsuccessful
accounts-password-reset-unsuccessful-message =
   El enlace de restablecimiento de contraseña no es válido, posiblemente
   porque ya fue usado. Solicita un nuevo enlace.



# Page title for completed page
accounts-password-reset-complete-page-title = Restablecimiento de contraseña completado

# Message shown when password reset is complete
accounts-password-reset-complete-message-html =
    Tu contraseña ha sido restablecida.
    Ya puedes <a href="{ $login_url }">iniciar sesión</a>.


## Change password page.

# Page title
accounts-password-change-page-title = Cambiar contraseña

# Instructions before form.
accounts-password-change-instructions = Introduce tu contraseña actual, y la nueva contraseña dos veces:

# Caption on button that will change password.
accounts-password-change-button = Cambiar contraseña

# Caption on password field
accounts-new-password = Nueva contraseña

# Caption on password confirmation field
accounts-new-password-confirmation = Nueva contraseña (confirmación)

# If old password was entered incorrectly
accounts-old-password-incorrect = Tu contraseña actual es incorrecta

# Caption on old password field
accounts-old-password = Contraseña actual

## Change password completed page.

# Title
accounts-password-change-done-title = Cambio de contraseña completado

# Body text
accounts-password-change-done-body = Tu contraseña ha sido actualizada


## Password reset email

accounts-password-reset-email-subject = Restablecimiento de contraseña en LearnScripture.net

accounts-password-reset-email =
   Hola { $username },

   Hemos recibido una solicitud de restablecimiento de contraseña
   para tu cuenta en learnscripture.net. (Si no lo has hecho tú,
   puedes ignorar este mensaje).

   Visita este enlace para actualizar tu contraseña:

   { $reset_url }

   ¡Gracias por usar nuestro sitio!

   El equipo de LearnScripture.net
