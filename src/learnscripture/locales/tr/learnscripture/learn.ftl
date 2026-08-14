### Learn page:

# Page title
learn-page-title = Çalışma

## Navbar:

# Link that takes the user back to the dashboard
learn-dashboard-link = Ön panel

# Link that takes the user back to where they came from
learn-return-link = Geri git


# This is shown in the top progress bar for a 'review' session.
learn-review-progress-bar-caption = Tekrarlama:

# These are shown in the top bar when data is being saved/loaded
learn-data-working = İşlem yapılıyor...
                   .tooltip = Veriler aktarılıyor.

# Button that will attempt to re-connect with server after internet
# connection is lost.
learn-reconnect-with-server = Sunucyla bağlantı kur

# Displayed when recording some action failed.
# $item is a description of the action
learn-data-failed = Hata - { $item }

# Displayed when some action is in a queue
# $item is a description of the action
learn-data-in-queue = Sırada - { $item }


# Displayed when attempting to record an action
# $item is a description of the action
# $attempt is the current attempt number
# $total is the total number of attempts that will be made
learn-data-being-attempted = Toplam { NUMBER($total) } denemeden { NUMBER($attempt) } - { $item }

## Navbar - session stats info:

# Displayed before the session stats
learn-session-stats-today = Bugün:

# Tooltip for the 'items started today' stat
learn-items-started-today = Bugün başlanan ögeler

# Tooltip for the 'total items tested today' stat
learn-items-tested-today = Bugün kontrol edilen ögeler

## Points menu:

# Displayed as a caption for the points gained in the current learning session
learn-session-points-caption = Oturum puanı:

# Tooltip for the points icon
learn-points-icon-caption = Bu oturum esnasında kazandığınız puanlar

## Points menu - different reasons for getting points:

learn-initial-test = ilk test
learn-review-test = tekrarlama testi
learn-revision-completed = düzeltme tamam
learn-perfect-score-bonus = tam puan için BONUS!
learn-verse-fully-learned-bonus = ayeti tamamen bildiğiniz için BONUS!
learn-award-bonus = bonus ödül

## Navbar:
# Tooltip for the 'pin/unpin' icon
learn-pin-icon-caption = Menüyü tuttur/tutturma

# Displayed when the current user is not logged in, in place of their username
learn-guest = Misafir

## Loading:

# Displayed when initially loading
learn-loading = Yükleniyor

# Displayed when initially loading, but there is first data to be saved from a previous session
learn-syncing = Eşitleniyor


## Current verse section:

# Displayed as tooltip for the memory progress percentage value
learn-memory-progress-caption = Bu ayeti çalışmada ilerlemeniz


# Displayed as a tooltip for the toggle button that shows the previous verse
learn-toggle-show-previous-verse = Önceki ayetin tamamını göster veya gizle

learn-verse-options-icon-caption = Ayet seçenekleri


## Instructions section:

learn-read-text-html =
  <b>OKU:</b>
  Metnin tamamını okuyun (yüksek sesle yapılması önerilir) '{ learn-next-button-caption }' düğmesine basınız.

learn-read-for-context-html =
  <b>OKU:</b>
  Bağlamı ve kısmın fikir akımını anlayabilmek için bu ayeti okuyun.

learn-read-and-recall-html =
  <b>OKU ve HATIRLA:</b>
  Okurken boşlukları hafızanızdaki bilgileri kullanarak doldurun. Hatırlayamadığınız kelimeleri göstermek için üzerine basınız.

# Displayed when the current test is just a practice test
learn-practice-test-note-html =
  <b>ALIŞTIRMA</b> testi. Puanlar sayılmaz.

learn-full-word-test-html = <b>TEST:</b> Hafızanızı test edin! Metni klavyenizle girin. Her kelimeden sonra boşluk tuşuna bazınız.

learn-you-dont-need-perfect-spelling = Tam puan almak için kelime imlasını tam tutturmanıza gerek yok.

learn-first-letter-test-html =  <b>TEST: </b> Hafızanızı test edin! Her kelimenin <b>ilk harfini</b> klavyenizle girin.

learn-choose-from-options-test-html = <b>TEST:</b> Hafızanızı test edin! Her bir kelimeyi gösterilen öğeleri kullanarak sırasıyla seçiniz.

# Test result.
# $score is the accuracy as a percentage.
# $comment is one of the comments below.
learn-test-result-html = <b>SONUÇLAR:</b> <b>{ NUMBER($score) }</b> puan aldınız - { $comment }

# Comment for better than 98%
learn-test-result-awesome = mükemmel!

# Comment for better than 96%
learn-test-result-excellent = harika!

# Comment for better than 93%
learn-test-result-very-good = çok iyi.

# Comment for better than 85%
learn-test-result-good = iyi.

# Comment for less than 85%, or when we are suggesting to try again.
learn-test-result-try-again = tekrar deneyelim!


# Shows the progress of the verse as a percentage
# $progress is the percentage
# $direction is 'forwards' if they are making progress or 'backwards' if they went back.
# If $direction is 'backwards' then $progress is negative.
learn-verse-progress-result-html =
    <b>İLERLEME:</b>
    { $direction ->
      *[forwards]   +{ NUMBER($progress) } ↗
       [backwards]   { NUMBER($progress) } ↘
    }

learn-verse-progress-complete-html =  <b>İLERLEME:</b> %100 tamam. İyi iş başardınız!

## Action choices:

learn-next-button-caption = Sonraki

learn-back-button-caption = Önceki

# Indicates a verse is fully learned
learn-verse-fully-learned = Çalışma tamam


# Displayed under 'practice' button, to indicate it will happen right now.
learn-see-again-now = Şimdi


# Displayed when a verse will be seen again in less than 1 hour
learn-see-again-less-than-an-hour = 1 saaten az

# Displayed when a verse will be seen again after between 1 and 24 hours.
# $hours is the number of hours
learn-see-again-hours = { NUMBER($hours) } saat

# Displayed when a verse will be seen again after between 1 and 7 days
# $days is the number of days
learn-see-again-days = { NUMBER($days) } gün

# $weeks is the number of weeks
learn-see-again-weeks = { NUMBER($weeks) } hafta

# Displayed when a verse will be seen again after several months
# $months is the number of months
learn-see-again-months = { NUMBER($months) } ay

## Verse options menu:

learn-skip-this-verse = Ayeti şimdilik atla

learn-skip-this-question = Soruyu şimdilik atla

learn-stop-learning-this-verse = Ayet çalışmasını durdur

learn-stop-learning-this-question = Soru çalışmasını durdur

learn-reset-progress = İlerlemeyi sıfırla

learn-test-instead-of-read = Okuma yerine test et

## Buttons under verse:

# Button for getting a hint.
# $used is the number of hints used so far,
# $total is the number of hints available,
# so it looks like "Use hint (1/2)"
learn-hint-button = İpucu kullan ({ NUMBER($used) }/{ NUMBER($total) })

# Button used to accept and go to next verse
learn-next-button = Tamam

# Button used to choose to practice a verse
learn-practice = Çalış

# Button used to practice a verse for a second/third time.
learn-practice-again = Tekrar çalış

# Button used to choose to see a verse sooner that normal schedule
learn-see-sooner = Daha erken göster

## Help section:

# Link that toggles the help section to be visible
learn-help = Yardım
           .tooltip = Yardımı göster

learn-take-the-help-tour = Site tanıtım turuna katıl.

learn-you-can-finish = Tekrarlama veya çalışma oturumuna yukarıdaki geri dön
  düğmesine basarak istediğinizde devam edebilirsiniz.

learn-keyboard-navigation-help = Klavye ile ilerleme (sadece fiziksel klayeler için,
  dokunmatik ekranlar için değil): Tab tuşu veya Shift+Tab tuşlarını kullanarak
  oğelerin dolaşıp Enter tuşuna basarak çalıştırabilirsiniz. Renkli bir kenar
  seçili ögeyi gösterir.

learn-button-general-help = En büyük olasılıkla kullanılacak düğme seçili olup
  renkli kenar ile gösterilir.

# The '<a>' and '</a>' wrap the text that will become a hyperlink to change preferences
learn-you-can-change-your-testing-method-html =
    Test metodunu istediğinizde <a>ayarlar</a> sayfasından değiştirebilirsiniz.

# The '<a>' and '</a>' wrap the text that will become a hyperlink to change preferences
learn-on-screen-testing-not-available-html =
    Özür dileriz! Seçili ayetin bu çeviride ekran testi mevcut değildir.
    <a>Ayarlar</a> sayfasını kullanarak farklı bir test seçeneğini belirleyin.

## Help tour:

# Button to finish the tour (at any point)
learn-help-tour-exit = Gezintiyi kapat

# Button to go to previous step in help tour
learn-help-tour-previous = Önceki

# Button to go to next step in help tour
learn-help-tour-next = Sonraki

# Button that closes the help tour at the end
learn-help-tour-finish = Bitir

# First message shown in help tour
learn-help-tour-hello =
    Selam! Bu gezinti size çalışma sayfası arabirimini tanıtır.

learn-help-tour-dashboard-link =
    Sol üst köşedeki linki kullanarak istediğinizde ön panoya dönebilirsiniz.

learn-help-tour-progress-bar =
    İlerleme çubuğu ayeti ilk defa çalışırken veya tekrarlama oturumundaki ilerlemenizi gösterir.

learn-help-tour-total-points =
    Seçili ayet dizisini çalışırken kazandığınız toplam puan burada gösterilir.

learn-help-tour-create-account =
    Puan kazanabilmek için bir hesap oluşturmalısınız (ön paneldeki linki kullanınız).

learn-help-tour-open-menu =
    Daha çok detay görüntülemek için menü başlığına basınız veya tıklayınız.

learn-help-tour-pin-menu =
    Bu menüyü büyük ekranlarda yana veya küçük ekranlarda üste sabitleyebilirsiniz.

learn-help-tour-close-menu =
    Menüyü kapatmak için menü başlığına basınız.

learn-help-tour-problem-saving-data =
    Verilerinizi kaydederken bir hata oluşsursa, hata burada görüntülenir. Daha bilgi edinmek için menü başlığına basınız.


learn-help-tour-internet-connection-cut =
    Internet bağlantınız kesilirse kaygılanmanıza gerek yok. Çalışmaya devam edebilirsiniz. Internete yeninden bağlandığınızda verileri kaydedebilirsiniz.

learn-help-tour-new-verses =
    Bugün çalışmaya başladığınız ayet sayısı burada görüntülenir. LearnScripture.net’e yeni başlamış iseniz, doğru çalışma hızını bulmak biraz zaman alabilir. Günlük bir ayeti öğrenmeye ne dersiniz?

learn-help-tour-tested-verses =
    Bugün test olduğunuz ayetlerin sayısı.

learn-help-tour-preferences =
    Seçeneklerinizi istediğinizde buradan ayarlayabilirsiniz.

learn-help-tour-verse-progress =
    Çalıştığınız her ayetın yaklaşık ilerlemesi burada görüntülenir.

learn-help-tour-verse-options =
    Bu menü seçili ayet için ek seçenekleri görüntülenir.

learn-help-tour-finish-test =
   Testinizi bitirdiğinizde, aldığınız sonuç ayet çaılışmasındaki ilerlemenizi belirler ve ne zaman tekrarlanacağını saptar. Ayeti ne zaman tekrar göreceğiniz belirten bir mesaj her bir ayeti ne zaman tekrar göreceğinizi gösterir.

learn-help-tour-end =
    Şimdilik bu kadar. Gezimize katıldığınız için teşekkür ederiz! Geziyi istediğinizde tekrarlayabilirsiniz (“Yardım” bölümüne bakınız.)

## Confirmation messages:

learn-confirm-leave-page-failed-saved =
   Kaydedilmemiş veri mevcuttur. Bu sayfadan ayrılırsanız bu veriler kaybolacaktır. Devam etmek istiyor musunuz?

learn-confirm-leave-page-save-in-progress =
   Veri kaydedilmektedir. Bu sayfadan ayrılırsanız bu veriler kaybolacaktır. Devam etmek istiyor musunuz?

learn-confirm-reset-progress =
   Bu ögedeki ilerlemeniz sıfırlanacaktır. Devam etmek istiyor musunuz?

## Saving data - descriptions of different data items being saved:

# Marking an item as done. $ref is a verse reference (or catechism reference)
learn-save-data-item-done = Tamamlanmış olarak tanımlandı - { $ref }

# Saving score for item. $ref is a verse reference (or catechism reference)
learn-save-data-saving-score = Puan kaydediliyor - { $ref }

# Recording that item was read. $ref is a verse reference (or catechism reference)
learn-save-data-read-complete = Okuma kaydediliyor - { $ref }

# Recording that item was skipped. $ref is a verse reference (or catechism reference)
learn-save-data-recording-skip = Atlanmış öge kaydediliyor - { $ref }

# Recording that an item was cancelled. $ref is a verse reference (or catechism reference)
learn-save-data-recording-cancel = İptal edilmiş öge kaydediliyor - { $ref }

# Recording that progress was reset for an item. $ref is a verse reference (or catechism reference)
learn-save-data-recording-reset-progress = { $ref } için ilerleme kaydediliyor

# Recording that an item was marked for being reviewed sooner. $ref is a verse reference (or catechism reference)
learn-save-data-marking-review-sooner = { $ref } ögesi daha sık tekrarlamak üzere ayarlandı

# Loading verses etc.
learn-loading-data = Çalışılacak ögeler yükleniyor...


## Error messages

# Error that normally appears only if there is an internet connection problem.
# $errorMessage gives a more specific error message.
learn-items-could-not-be-loaded-error =
    Çalışılacak ögeler yüklenemedi (hata bildirimi: { $errorMessage }). İnternet bağlantınızı kontrol edin!
