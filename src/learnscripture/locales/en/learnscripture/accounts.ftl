### User accounts related text.

## Account information.

# Caption for username field
accounts-username = Username

# Caption for first name field, editable on account details page
accounts-first-name = First name

# Caption for last name field, editable on account details page
accounts-last-name = Last name


# Caption for full name field (combined first name and last name)
accounts-full-name = Name

# Caption for email field
accounts-email = Email

# Caption for password field
accounts-password = Password

# Caption for date the user joined the website
accounts-date-joined = Date joined

# Caption for "user is under 13 years old" field
accounts-under-13 = Under 13 years old

# Caption for user field that enables the comment system (true/false)
accounts-enable-commenting = Enable comment system

# Caption for 'account' field
accounts-account = Account

# Caption for the Account 'date created' field
accounts-date-created = Date created

## Account details page.

# Page title
accounts-details-page-title = Account details

# Sub title
accounts-details-personal-info-subtitle = Personal information

# Sub title indicating data that won't be publicly visible
accounts-details-private-info-subtitle = Private

# Sub title indicating data that will be publicly visible
accounts-details-public-info-subtitle = Public

# Success message when details are updated
accounts-details-updated = Account details updated, thank you


## Preferences.

# Page title
accounts-preferences-title = Preferences

# Shown at top of preferences page
accounts-preferences-instructions = Enter your preferences and press '{ accounts-preferences-save-button }' to continue.

# Additional notes about preferences
accounts-preferences-instructions-additional-notes =
    All preferences can be changed later, and the Bible version
    can be chosen on a verse-by-verse basis


# Caption for the account 'default bible version' field
accounts-default-bible-version = Default bible version

# Caption for choice of testing method (how verses are tested)
accounts-testing-method = Testing method

accounts-type-whole-word-testing-method = Type whole word - most thorough

accounts-type-first-letter-testing-method = Type first letter - faster

accounts-choose-from-list-testing-method = Choose from word list - recommended for  handheld devices. Not available for all translations.

accounts-desktop-testing-method = Desktop testing method

accounts-touchscreen-testing-method = Touchscreen testing method


# Caption for 'enable animations' field
accounts-enable-animations = Enable animations

# Caption for 'enable sounds' field
accounts-enable-sounds = Enable sounds

# Caption for 'enable vibration' field
accounts-enable-vibration = Vibrate on mistakes
                          .help-text = Depends on device capabilities.


# Caption for choice of interface colour theme
accounts-interface-theme = Interface theme

# Name of interface theme that is a slate blue colour
accounts-slate-theme = Slate

# Name of interface theme that is a neon pink
accounts-bubblegum-pink-theme = Bubblegum pink

# Name of interface theme that is a neon green
accounts-bubblegum-green-theme = Bubblegum green

# Name of interface theme that is dark with 'Space' colours
accounts-space-theme = Space

# Caption for 'interface language' field
accounts-interface-language = Interface language

# Caption for button to save changes to preferences
accounts-preferences-save-button = Save

# Caption for button to cancel changes and close preferences dialog
accounts-preferences-cancel-button = Cancel

## Account notifications.

# Notification when user is invited to join a group,
# $user is the person who invited them,
# $group is the name of the group
accounts-invitation-received-html = { $user } invited you to join the group { $group }


## Signup.

# Title of 'create account'/'signup' page
accounts-signup-title = Create account

# Message displayed if the user goes to the sign up page but is already logged in.
accounts-already-logged-in-html = You are already signed in as <b>{ $username }</b>. You should logout if you want to create a new account.

accounts-signup-agree-to-terms-of-service-html =
        By creating an account, you are agreeing to our
        <a href="/terms-of-service/" target="_blank">terms of service</a> and
        <a href="/privacy-policy/" target="_blank">privacy policy</a>.
        Please note that children under the age of 13 may not create
        an account, but a parent may create an account for them,
        and must tick the corresponding checkbox above.

accounts-signup-parents-notice = Parents concerned about children having contact with other
        people on the internet via the commenting system should
        disable the commenting option above.

# Button to create account after filling in form
accounts-signup-create-account-button = Create account


# Message displayed if user tries to put invalid characters in their chosen username
accounts-username-validation = This value may contain only letters, numbers and these characters: . + - _

# Message displayed if password is too short
accounts-password-length-validation = The password must be at least { $length } characters

# Message displayed if user tries to choose a username that is already taken
accounts-username-already-taken = Account with this username already exists

# Help text for email field when signing up
accounts-email-help-text = Private. Needed for password reset.

# Notification when a user signs up
accounts-signup-welcome-notice = Account created - welcome { $username }!


## Login.

# Title of log-in page
accounts-login-title = Login

# Caption for the email/username input box
accounts-login-email-or-username = Email or username

# Message shown when the user enters a wrong username, email or password
accounts-login-no-matching-username-password = Can't find an account matching that username/email and password

# Message shown when the user enters an email address to log in, but multiple accounts exist for that email address
accounts-login-multiple-accounts = Multiple accounts for this email address - please enter your username instead

# Message shown when the user tries to reset their password, but enters an email address that isn't found
accounts-reset-email-not-found = That email address doesn't have an associated user account. Are you sure you've registered?

# Shown when trying to change or set password and the passwords don't match
accounts-password-mismatch = The two password fields didn't match.

## Password reset.

# Page title for start page
accounts-password-reset-start-page-title = Password reset started

accounts-password-reset-start-email-sent =
    We've e-mailed you instructions for setting your password to the e-mail
    address you submitted. You should receive it shortly.

# Page title for main reset page
accounts-password-reset-page-title = Password reset

# Instructions at top of password reset new password form
accounts-password-reset-new-password-instructions =
    Please enter your new password twice so we can verify you typed it in correctly.


# Title password reset was unsuccessful
accounts-password-reset-unsuccessful-title = Password reset unsuccessful

# Message shown when password reset was unsuccessful
accounts-password-reset-unsuccessful-message =
   The password reset link was invalid, possibly because it has already
   been used. Please request a new password reset.



# Page title for completed page
accounts-password-reset-complete-page-title = Password reset complete

# Message shown when password reset is complete
accounts-password-reset-complete-message-html =
    Your password has been set.
    You may go ahead and <a href="{ $login_url }">log in</a> now.


## Change password page.

# Page title
accounts-password-change-page-title = Change password

# Instructions before form.
accounts-password-change-instructions = Please enter your old password, and your new password twice:

# Caption on button that will change password.
accounts-password-change-button = Change password

# Caption on password field
accounts-new-password = New password

# Caption on password confirmation field
accounts-new-password-confirmation = New password confirmation

# If old password was entered incorrectly
accounts-old-password-incorrect = Your old password was entered incorrectly. Please enter it again.

# Caption on old password field
accounts-old-password = Old password

## Change password completed page.

# Title
accounts-password-change-done-title = Password change successful

# Body text
accounts-password-change-done-body = Your password was changed.


## Password reset email

accounts-password-reset-email-subject = Password reset on LearnScripture.net

accounts-password-reset-email =
   Hi { $username },

   You're receiving this email because you requested a password
   reset for your account on learnscripture.net. (Just ignore
   this email if you didn't).

   Please go to the following page and choose a new password:

   { $reset_url }

   Thanks for using our site!

   The LearnScripture.net team
