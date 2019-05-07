### Dashboard page
# Title of 'dashboard' page
dashboard-page-title = Ön Panel

# Notice that appears for guest users who haven't created an account yet
dashboard-remember-to-create-an-account-html =
    <b><a href="{ $signup_url }">Hesap oluşturmayı lütfen unutmayınız!</a></b>
    Oluşturmazsanız ilerlemeniz kaydedilmeyecek. Hesabı oluşturmak ücretsizdir
    ve birkaç saniye içinde gerçeklerştirilir. Hesabınız olursa, birçok özelliğe
    erişiminiz sağlanır; örn. rozetler, gruplar, lider tahtası, ve istatistik
    sayfaları. Misafir verileriniz { DATETIME($expires) } tarihinde silinecektir.


## Add to home screen section.
# Sub title
dashboard-add-to-home-screen-title = Ana ekrana ekle

# Button for adding
dashboard-add-to-home-screen-button = Ekle

# Explanation
dashboard-add-to-home-screen-explanation = Daha iyi bir deneyim için bu uygulamayı cihazınızın ana ekranına ekleyebilirsiniz.

# Instructions for adding to homescreen on browsers that use a menu bar icon for this.
# Text is followed by an image
dashboard-add-to-home-screen-menu-bar-instructions = Sayfayı eklemek için menü çubuğunda şu imgeyi tıklayın:


## Unfinished session section.

# Sub title
dashboard-continue-title =
    Devam et

dashboard-unfinished-notice = Açık bir oturumunuz mevcuttur.

dashboard-unfinished-notice-part-2 = Kaydedilmemiş verileri kaydetmek için oturuma devam edin.

# Caption for button that will continue the session
dashboard-continue-button = Devam et

## Heatmap section.

dashboard-learning-events = Çalışma eylemleri

## Review section.

# Sub title
dashboard-review-title = Tekrarlama

# Button for reviewing a whole passage
dashboard-review-whole-passage-button = Kısmın tamamı

# Button for reviewing one section of a passage.
# $verse_count is the number of verses in that section.
dashboard-review-one-section-button = Tek bir kısım ({ $verse_count } ayet)

# Button for reviewing a verse or set of verses, or a catechism question
dashboard-review-button = Tekrarla

# Button for cancelling learning a verse/passage
dashboard-cancel-learning = İptal

# Note shown when the whole passage is due for review
# $verse_count is the number of verses in the passage
dashboard-passage-due-for-review = Bu kısmı tekrarlama vakti geldi ({ $verse_count } ayet).

# Note shown when part of a passage verse set is due for review.
# $needs_testing_count is the number that are due for review,
# $total_verse_count is the total number of verses in the passage
dashboard-passage-part-due-for-review = Bu kısmın bir bölümünü tekrarlama vakti geldi ({ $needs_testing_count }/{ $total_verse_count } ayet).

# Indicates the number of verses due for review (separate from the passage verse sets)
dashboard-verses-for-review-count = Tekrarlama vakti gelen { $count } ayet var.

# Displayed before a list of verse references that are due for review or learning
dashboard-verses-coming-up = Sonraki ayetler:

# Indicates the number of catechism questions due for review
dashboard-catechism-questions-for-review-count = Tekrarlamanız gereken { $count } soru mevcut.

# Message shown if there is nothing in the general queue due for reviewing. (Excludes passage verse sets)
dashboard-general-queue-empty = Genel sıralamada tekrarlaması gereken öge yoktur.

# Message about the next verse due for review.
# $title is the verse reference or catechism title,
# $timeuntil is a string like "5 minutes" or "3 hours"
dashboard-next-item-due-html = Tekrarlaması gereken sonraki öge: { $timeuntil } sonra <b>{ $title }</b>


## Learn section.

# Sub title
dashboard-learn-title = Çalış

# Button to start learning a passage
dashboard-learn-start-learning-button = Çalışmaya başla

# Button to continue learning a passage (they have already started at least one verse)
dashboard-learn-continue-learning-button = Çalışmaya devam et

# Message displayed for a passage set that is in the user's queue
# for learning (but that haven't started yet)
dashboard-passage-queued = You've queued this passage for learning.

# Message on a passage verse set indicating the number of items learnt
# and still not started.
dashboard-passages-youve-seen-verses ={ $tested_total } ayet çalışmış bulunyorsunuz.
     Çalışmanız gereken { $untested_total } ayet kaldı.

# Message on a passage verse set indicating the number of items learnt
# and still not started, inluding info about those that are due for review.
dashboard-passages-youve-seen-verses-with-review-due-html = { $tested_total } ayet görmüş bulunyorsunuz.
    <b>{ $needs_review_total } ayet tekrarlama için hazır</b>
    ve { $untested_total } daha başlanmadı.


# Sub title for verses that aren't part of a verse set
dashboard-learn-other-verses = Diğer ayetler

# Shows number of verses in queue for learning
dashboard-queued-verses = Çalışmanız için { $count } yeni ayet sıralandı.

# Shows number of verses in a particular set in queue for learning
dashboard-queued-verses-in-set = Bu dizinde çalışmanız için { $count } yeni ayet sıralandı.

# Button to learn a verse or queue of verses
dashboard-learn-button = Çalış

# Button to remove items from the queue of verses to learn
dashboard-clear-queue-button = Sıfırla

# Indicates the total number of questions in a catechism that has been queued for learning
dashboard-catechism-question-count = Çalışmanız için bu ilmihalde { $count } soru sıralandı.

# Indicates the number of questions in a catechism that have been started, and how many remain.
dashboard-catechism-learnt-and-remanining-count = { $started_count } soru görmüş bulunyorsunuz.
   Kalan { $remaining_count } soru var.

# Message displayed when there are no passages, verses or catechisms queued for learning
dashboard-learn-nothing-in-queue = Çalışmak için sırada öğe yoktur.

# Confirmation prompt after clicking 'clear queue' button for verses
dashboard-remove-verses-from-queue-confirm = Seçili ayetler çalışma sırasından çıkarılacaktır. Bunları çalışabilmek için ayetleri veya ayet dizinleri bir daha seçmeniz gerekecek. Devam edelim mi?

# Confirmation prompt after clicking 'cancel' button for a catechism
dashboard-remove-catechism-from-queue = Seçili ilmihal soruları çalışma sırasından çıkarılacaktır. Bunları çalışabilmek için ilmihali bir daha seçmeniz gerekecek. Devam edelim mi?

# Confirmation prompt after clicking 'cancel' for a passage verse set
dashboard-cancel-passage-confirm = Seçili çeviride kısım çalışması sonlandırılacak. Test puanları kaydedilecek. Devam edelim mi?

## 'Choose' section.

# Sub title
dashboard-choose-title = Çalışma Seçimi

dashboard-choose-link-html = Yukarıdaki çalışmayı bitirdikten sonra, <a href="{ $url }">çalışmak için yeni ayetler veya kısım seçiniz</a>.

## Right column.

dashboard-todays-stats-title = Günlük istatistikler

# Indicates the number of new verses the user has started today
dashboard-todays-stats-new-verses-begun = Başladığınız yeni ayetler: { $new_verses_started }

# Indicates the number of verses the user has been tested on today
dashboard-todays-stats-total-verses-tested = Çalışılmış toplam ayet: { $total_verses_tested }

# Sub title for the list of groups the user is a member of
dashboard-your-groups-title = Gruplarınız

# Link to see all groups the user is a member of, appears at bottom of a truncated list
dashboard-groups-see-all = (hepsini göster)

dashboard-view-other-groups-link = Diğer grupları gez

dashboard-why-not-join-a-group-html = Herhangi bir gruba üye değilsiniz. Bir <a href="{ $url }">gruba katılmak</a> ister misiniz?

## News section.

# Sub title
dashboard-news-title = Haberler

# Link to the news page
dashboard-more-news-link = Daha fazla haber görüntüle...
