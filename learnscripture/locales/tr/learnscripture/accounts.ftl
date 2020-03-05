### User accounts related text.

## Account information.

# Caption for username field
accounts-username = Kullanıcı Adı

# Caption for first name field, editable on account details page
accounts-first-name = Adı

# Caption for last name field, editable on account details page
accounts-last-name = Soyadı


# Caption for full name field (combined first name and last name)
accounts-full-name = Adı

# Caption for email field
accounts-email = e-Posta

# Caption for password field
accounts-password = Parola

# Caption for date the user joined the website
accounts-date-joined = Katılım tarihi

# Caption for "user is under 13 years old" field
accounts-under-13 = 13 yaşından küçük

# Caption for user field that enables the comment system (true/false)
accounts-enable-commenting = Yorumları etkinleştir

# Caption for 'account' field
accounts-account = Profil

# Caption for the Account 'date created' field
accounts-date-created = Oluşturma tarihi

## Account details page.

# Page title
accounts-details-page-title = Profil detayları

# Sub title
accounts-details-personal-info-subtitle = Şahsi bilgiler

# Sub title indicating data that won't be publicly visible
accounts-details-private-info-subtitle = Özel

# Sub title indicating data that will be publicly visible
accounts-details-public-info-subtitle = Herkese açık

# Success message when details are updated
accounts-details-updated = Profil bilgileri güncellendi


## Preferences.

# Page title
accounts-preferences-title = Tercihler

# Shown at top of preferences page
accounts-preferences-instructions = Tercihlerinizi girdikten sonra devam etmek için '{ accounts-preferences-save-button }' düğmesine basınız.

# Additional notes about preferences
accounts-preferences-instructions-additional-notes =
    Tüm tercihler sonradan değiştirilebilir. İstenilen Kutsal
    Kitap çevirisi her bir ayete göre ayrı ayrı ayarlanabilir.

# Caption for the account 'default bible version' field
accounts-default-bible-version = Varsayılan Çeviri

# Caption for choice of testing method (how verses are tested)
accounts-testing-method = Test usulü

accounts-type-whole-word-testing-method = Tüm kelimeyi gir - en kapsamlı

accounts-type-first-letter-testing-method = İlk harfi gir - daha hızlı

accounts-choose-from-list-testing-method = Kelimeyi listeden seç - mobil cihazlar için önerilir. Yalnızca İngilizce çeviriler için geçerlidir.

accounts-desktop-testing-method = Klavye-fareli test usulü

accounts-touchscreen-testing-method = Dokunmaktik test usulü


# Caption for 'enable animations' field
accounts-enable-animations = Geçişleri etkinleştir

# Caption for 'enable sounds' field
accounts-enable-sounds = Sesleri etkinleştir

# Caption for 'enable vibration' field
accounts-enable-vibration = Hata yapınca titrettir
                          .help-text = Cihaz özelliğine bağlıdır


# Caption for choice of interface colour theme
accounts-interface-theme = Arabirim teması

# Name of interface theme that is a slate blue colour
accounts-slate-theme = Taş mavisi

# Name of interface theme that is a neon pink
accounts-bubblegum-pink-theme = Çılgın pembe

# Name of interface theme that is a neon green
accounts-bubblegum-green-theme = Kamaştıran yeşil

# Name of interface theme that is dark with 'Space' colours
accounts-space-theme = Uzayın siyahı

# Caption for 'interface language' field
accounts-interface-language = Arabirm dili

# Caption for button to save changes to preferences
accounts-preferences-save-button = Kaydet

# Caption for button to cancel changes and close preferences dialog
accounts-preferences-cancel-button = İptal

## Account notifications.

# Notification when user is invited to join a group,
# $user is the person who invited them,
# $group is the name of the group
accounts-invitation-received-html = { $user } adlı kullanıcı sizi { $group } adlı gruba davet etti


## Signup.

# Title of 'create account'/'signup' page
accounts-signup-title = Hesap oluştur

# Message displayed if the user goes to the sign up page but is already logged in.
accounts-already-logged-in-html =  <b>{ $username }</b> kullancı ismiyle zaten giriş yaptınız. Yeni bir hesap oluşturmak için <a href="#" class="logout-link">Çıkış</a> yapınız.

accounts-signup-agree-to-terms-of-service-html =
        Bir hesabı oluşturduğunuzda
        <a href="/terms-of-service/" target="_blank">kullanıcı koşullarına</a> ve
        <a href="/privacy-policy/" target="_blank">gizlilik politikasına</a>
        tabi olmaya kabul ediyorsunuz.
        13 yaşından küçük çocuklar hesap oluşturamaz. Ebeveynleri onlar için
        hesap oluşturabilir, ancak küçük yaşı belirten kutucuğu işaretlemeliler.

accounts-signup-parents-notice = Çocukların internet aracılığıyla başkalarıyla irtibat kurmasını
        istemeyen ebeveynler yukarıdan yorumları devredışı
        birakabilir.

# Button to create account after filling in form
accounts-signup-create-account-button = Hesabı oluştur


# Message displayed if user tries to put invalid characters in their chosen username
accounts-username-validation = Bu alanda sadece harfler, rakamlar ve . + - _ karakterleri girilebilir.

# Message displayed if password is too short
accounts-password-length-validation = Parola en az { $length } karakter uzunluğunda olmalıdır.

# Message displayed if user tries to choose a username that is already taken
accounts-username-already-taken = Bu kullanıcı adı zaten bir hesap için kullanılmıştır

# Help text for email field when signing up
accounts-email-help-text = Özel tutulur. Bildirimler ve parola değişimi için gereklidir

# Notification when a user signs up
accounts-signup-welcome-notice = Hesabınız oluşturuldu, { $username }. Hoş geldiniz!


## Login.

# Title of log-in page
accounts-login-title = Giriş yap

# Caption for the email/username input box
accounts-login-email-or-username = e-Posta veya kullanıcı adı


# Message shown when the user enters a wrong username, email or password
accounts-login-no-matching-username-password = Bu e-Posta adresi veya kullanıcı adı veya parola ile eşleşen bir hesap bulunamadı

# Message shown when the user enters an email address to log in, but multiple accounts exist for that email address
accounts-login-multiple-accounts = Bu e-Posta adresine birden fazla hesap bağlıdır. Lütfen kullanıcı adınızı giriniz.

# Message shown when the user tries to reset their password, but enters an email address that isn't found
accounts-reset-email-not-found = Girdiğiniz e-Posta adresine bağlı bir hesap bulunamadı. Sitemize kaydoldunuz mu?

# Shown when trying to change or set password and the passwords don't match
accounts-password-mismatch = Parolalar birbiriyle eşleşmiyor.

## Password reset.

# Page title for start page
accounts-password-reset-start-page-title = Parola değiştirme işlemi

accounts-password-reset-start-email-sent =
    Parola değiştirme yönergelerini girdiğiniz e-Posta adresine
    gönderdik. Birazdan giriş kutunuza düşmesi gerekir.

# Page title for main reset page
accounts-password-reset-page-title = Parola değiştirme

# Instructions at top of password reset new password form
accounts-password-reset-new-password-instructions =
    Doğrulamak için parolanızı lütfen tekrar giriniz.


# Title password reset was unsuccessful
accounts-password-reset-unsuccessful-title = Parola değiştirilemedi

# Message shown when password reset was unsuccessful
accounts-password-reset-unsuccessful-message =
   Kullandığınız parola değiştirme linki geçersizdir. Önceden kullanılmış
   olabilir. Lütfen yeni bir sıfırlama linki talep edin.



# Page title for completed page
accounts-password-reset-complete-page-title = Parola başarıyla değiştirildi

# Message shown when password reset is complete
accounts-password-reset-complete-message-html =
    Parolanız ayarlandı.
    <a href="{ $login_url }">Siteye giriş yapabilirsiniz</a>.


## Change password page.

# Page title
accounts-password-change-page-title = Parola değiştirme

# Instructions before form.
accounts-password-change-instructions = Eski parolanızı girip yeni parolanızı iki kere giriniz.

# Caption on button that will change password.
accounts-password-change-button = Parolayı değiştir

# Caption on password field
accounts-new-password = Yeni parola

# Caption on password confirmation field
accounts-new-password-confirmation = Yeni parolayı doğrula

# If old password was entered incorrectly
accounts-old-password-incorrect = Eski parolanız hatalı girildi. Lütfen parolayı tekrar giriniz.

# Caption on old password field
accounts-old-password = Eski parola

## Change password completed page.

# Title
accounts-password-change-done-title = Parola  değiştirme başarılı.

# Body text
accounts-password-change-done-body = Parolanız başarıyla değiştirildi.


## Password reset email

accounts-password-reset-email-subject = LearnScripture.net sitesi için yeni parola

accounts-password-reset-email =
   Selam { $username }!

   LearnScripture.net sıtesine girebilmek için yeni bir parola
   oluşturma talebinde bulunduğunuz için bu e-Posta iletisini
   almış bulunuyorsunuz. (Talepte bulunmadıysanız bu iletiyi
   göz ardı edebilirsiniz.)

   Parolanızı ayarlamak için aşağıdaki linki tıklayınız:

   { $reset_url }

   Sitemizi kullandığınız için teşekkür ederiz.

   LearnScripture.net takımı
