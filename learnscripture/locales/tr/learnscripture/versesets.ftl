## Verse sets.

# Caption for the 'name' field of a verse set
versesets-name = Başlık

# Caption for the 'description' field of verse sets
versesets-description = Tanım

# Caption for the 'additional info' field of verse sets
versesets-additional-info = Ek bilgi

# Caption for the 'public' field when creating a Verse Set
versesets-public = Kamuoyuna aç (geri alınamaz)

## Searching and filtering verse sets.

# Caption for the search input box for searching for verse sets
versesets-search = Ara

# Caption for the filter to select type of verse set (selection or passage)
versesets-filter-type = Tür

# Caption for filtering by 'Selection' verse sets
versesets-filter-selection-caption = Seçili ayetler - bir tema veya konu hakkında özellikle seçilmiş ayetleri içerir

# Caption for filtering by 'Passage' verse sets
versesets-filter-passage-caption = Kısım - Kutsal Kitap bölümünden bir ayet dizisi

# Caption for showing all verse set types (selection and passage)
versesets-filter-all = Hepsi

# Caption for the sorting options of the verse sets
versesets-order = Sıralama

# Caption for ordering verse sets by most popular first
versesets-order-most-popular-first = En popüler üstte

# Caption for ordering verse sets by newest first
versesets-order-newest-first = En yeni üstte

## Viewing a verse set.

# Page title.
# $name is the name of the verse set being viewed.
versesets-view-set-page-title = Ayet dizini: { $name }

# Sub-title for list of verses in set
versesets-view-set-verses-title = Ayetler

# Message displayed when verse set is empty
versesets-view-set-no-verses = Bu dizinde ayet bulunmamaktadır.



# Sub-title for additional notes about the verse set
versesets-view-set-notes-title = Notlar

# Note about how to opt out of learning
versesets-view-set-how-to-opt-out = Bir ayet dizisini çalışırken bir ayeti öğrenmek istemezseniz çalışma sayfasında
          “{ learn-stop-learning-this-verse }” düğmesine basarak onu diziden çıkarabilirsiniz.

# Note about verse set being public
versesets-view-set-learning-is-public = Ayeti çalışma eylemi herkes tarafından görülebilir
        (ayet dizisinin ayarı özel olmadığı sürece)

# Prompt to change a verse set to a 'passage set'
versesets-view-set-change-to-passage-set = Bu ayet dizisi sırasıyla ilerleyen ayetleri içeriyor. Böyle bir dizi
      “kısım” dizisi olarak çalışılırsa daha iyi olur. Aşağıdaki
      düğmeye basarak ayet dizisini kısım dizisine dönüştürebilirsiniz:

# Button to change to passage set
versesets-view-set-change-to-passage-set-button = Kısım dizisine dönüştür


# Notice displayed when a 'selection' verse set is converted to a 'passage' verse set
versesets-converted-to-passage = Ayet dizini “kısım” dizisine dönüştürüldü.

# Button to edit the verse set being displayed
versesets-view-set-edit-button = Düzenle

# Sub-title for section with additional info about the verse set
versesets-view-set-info-title = Ayet dizini hakkında

# Indicates who put the verse set together.
versesets-view-set-put-together-by-html = { $username } tarafından hazırlandı

# Indicates when the verse set was created
versesets-view-set-date-created = { DATETIME($date_created) } tarihinde oluşturuldu.

# Shown when the verse set is private
versesets-view-set-private = Özel - sadece siz bu ayet dizisini görebilirsiniz.

# Sub-title for section about the user's use of this verse set
versesets-view-set-status-title = Durum

# Shown when the user isn't learning the verse set at all (in the given Bible version).
# $version_name is the name of a Bible version.
versesets-view-set-not-learning = Bu ayet dizisini { $version_name } çevrisinde çalışmıyorsunuz.

# Shown when the user has started learning all the verses in the verse set.
# $version_name is the name of a Bible version.
versesets-view-set-learning-all = Bu dizindeki ayetleri { $version_name } çevirisini kullanarak ezberlemektesiniz.

# Shown when the user has started learning some of the verses in the verse set.
# $started_count is the number they have started learning.
# $total_count is the total number of verses in the set.
# $version_name is the name of a Bible version.
versesets-view-set-learning-some = Toplam { $total_count } ayetten { $started_count } ayeti { $version_name } çevirisinde çalıştınız.

# Shown when the user has some verses in this set in their learning queue.
# $in_queue_count is the number of verses in their queue.
# $version_name is the name of a Bible version.
versesets-view-set-number-in-queue =
        Bu dizide { $version_name } çevirisinden { $in_queue_count } ayet
        alışmak üzere sizin için sıralandı.

# Beginning of section regarding removing verses from learning queue
versesets-view-set-remove-from-queue-start = Ayetleri diziden çıkarmak isterseniz:

# First method for removing verses from queue
versesets-view-set-remove-from-queue-method-1 =
        Ayetleri tek tek çalışma arabiriminden çıkarmak için ayeti görüntülenmesini bekleyip
        seçenekler menüsünden “{ learn-stop-learning-this-verse }”
        ögesini seçiniz.

# Second method for removing verses from queue, followed by a button to remove all
versesets-view-set-remove-from-queue-method-2 = veya hepsini birden sıradan çıkarabilirsiniz:

# Button to drop all verses from queue
versesets-view-set-drop-from-queue-button = Ayetleri sıradan çıkar

# Noticed displayed after the user chooses to remove some verses from their learning queue
versesets-dropped-verses = { $count } ayet çalışma sırasından çıkarıldı.


## Creating/editing verse sets.

# Page title for editing
versesets-edit-set-page-title = Ayet dizisini düzenle

# Page title for creating a selection set
versesets-create-selection-page-title = Seçili ayet dizisini oluştur

# Page title for creating a passage set
versesets-create-passage-page-title = Kısım dizisini oluştur

# Sub title when editing verse sets, for title/description fields
versesets-about-set-fields = Dizi hakkında

# Sub title when editing verse sets, for list of verses in set
versesets-verse-list = Ayet listesi

# Message displayed in verses when no verses have been added yet
versesets-no-verses-yet = Ayet henüz eklenmedi!

# Validation error message if user tries to create set with no verses
versesets-no-verses-error = Dizide ayet bulunmamaktadır.

# Success message when a verse set is saved
versesets-set-saved = “{ $name }” başlıklı ayet dizisi kayedildi!

# Sub title for the section with controls for adding verses
versesets-add-verses-subtitle = Tüm ayetler

# Caption on button for adding a verse to a verse set
versesets-add-verse-to-set = Diziye ekle

# Caption for the button that saves the edited/new verse set
versesets-save-verseset-button = Ayet dizisini kaydet

# Sub title for section that allows you to choose a passage
versesets-choose-passage = Kısmı belirle

versesets-natural-break-explanation =
  10 ayetten uzun olan kısımlarda fikirler arasındaki doğal aralıkları tanımlarsanız
  ezberlemek daha kolay olur. Bu aralıları yeni fikrin ilk ayetindeki
  “Kısmı böl” kutusunu işaretleyerek belirleyebilirsiniz.

# Explanation of 'breaks'
versesets-natural-break-explanation-part-2-html =
  <b>NOT:</b> Kısım bölmeleri <b>uzun</b> kısımları tanımlamak için ayet bölmelerine <b>ek olarak</b> tanımlanmıştır.
  Kısım bölmelerini eklemesenizde kısmı çalışırken ayetler tek tek görüntülenecektir.

# Heading for section break column
versesets-section-break = Kısmı böl

# Sub title for section with optional fields
versesets-optional-info = Ek bilgi (isteğe bağlı)

# Shown when the user enters a passage reference and there are other verse sets for that passage
versesets-create-duplicate-passage-warning = Seçili kısmı içeren şu diziler bulundu:

## Viewing user's own verse sets.

# Sub-title for section showing the list of verse sets the user is learning
versesets-you-are-learning-title = Çalıştığınız ayet dizileri

# Sub-title for section showing the list of verse sets the user created
versesets-you-created-title = Oluşturuğunuz ayet dizileri
