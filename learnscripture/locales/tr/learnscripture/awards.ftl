
## Awards/badges.

# Notification received when a user gets a new award/badge,
# $award is the award name (appears as a link)
awards-new-award-html = Yeni bir rozet kazandınız: { $award }.

# Notification received when a user gets a higher level for an award/badge
# $award is the award name (appears as a link)
awards-levelled-up-html = Rozetinizde yeni bir seviyeye geçtiniz: { $award }.

# Notification when there are points for an award that has been received.
# $points is the number of points given
awards-points-bonus =  Bonus puanlar: { $points }.

# Appears next to notification about new award, as shortcuts for
# telling other people about the award.
# $twitter is a link to Twitter.
# $facebook is a link to Facebook.
awards-tell-people-html = Arkadaşlarınızı bilgilendirin: { $facebook } { $twitter }

# Default message that is used for sharing about awards on twitter/facebook
# $award is the award name/description
awards-social-media-default-message = Ben bir rozet kazandım: { $award }

## Awards page.

# Page title
awards-page-title = Rozetler

awards-the-following-are-available = Alabileceğiniz rozetler


# Caption in table header for award name/icon
awards-award = Rozet

# Caption in table header for when the award was received
awards-date-received = Tarih

# Caption in table header for award icon
awards-icon = İmge

# Caption in table header for award description
awards-description = Tanım

# Caption in the table header for award points
awards-points = Puan

# Indicates the level of an award/badge
awards-award-level = seviye  { $level }

# Indicates the highest level that has so been achieved for the award
award-highest-level-achieved-html = Şimdiye kadar ulaşılan seviye: <b>{ $level } seviyesi</b>

# Link to page showing details about who has achieved the award,
# $name is the name/short description of the award
award-people-with-award = { $name } rozeti olan kişiler


## Individual award page.

# Page title,
# $name is the award name/short description
awards-award-page-title = Rozet - { $name }

# Heading for description of award
awards-description-subtitle = Tanım

# Heading for list of people who have achieved the award
awards-achievers-subtitle = Rozeti alanlar

# Indicates the highest level that can be achieved for an award
awards-award-highest-level = { $level } seviyesi ulaşabileceğiniz en yüksek seviyedir.

# Subtitle
awards-level-subtitle = { $level } seviyesi

# Indicates the number of people who have achieved the award at this level, followed
# by a list containing all those users
awards-level-achievers-all = Toplam { $count } kullanıcı:


# Indicates the number of people who have achieved the award at this level, followed
# by a list containing a sample of those users.
awards-level-achievers-truncated = Toplam { $count } kullanıcı, bunlara dahil:


# Link to page showing all badges
awards-all-available-badges = Alabileceğiniz tüm rozetler

# Link to page showing user's badges
awards-your-badges = Rozetlerim

# Subtitle for section describing the user's level for the award being described
awards-your-level = Eriştiğim seviye

# Used when the award has levels, and the user has the award at a certain level
awards-you-have-this-award-at-level = { $level } seviyesinde bu rozete sahipsiniz.

# Used when the award has does not have levels, and the user has the award.
awards-you-have-this-award = Bu rozete sahipsiniz.

# Used when the user doesn't have the award
awards-you-dont-have-this-badge = Bu rozete henüz sahip değilsiniz.

# Message used when trying to view some old awards
awards-removed = ‘{ $name }’ rozeti artık verilmemektedir.

## 'Student' award.

# Name
awards-student-award-name =
    Çırak

# General description
awards-student-award-general-description =
    Ayet çalışmaya başlayınca verilen ödül. Ödül dokuz seviyeden oluşup birinci seviye bir ayet için verilir. Dokuzuncu seviye ise Kutsal Kitap’ın tamamı için verilir.

# Description for a specific level
awards-student-award-level-n-description =
    En az { $verse_count ->
        [one] 1 ayet
       *[other] { $verse_count } ayet
    } çalışıldı.

# Specific description for level 9
awards-student-award-level-9-description =
    Learning the whole bible!


## 'Master' award.

# Name
awards-master-award-name =
    Usta

# General description
awards-master-award-general-description =
    Ayetleri 5 yıldız ile tamamen öğrenince verilen ödül. Ayetlerin gerçekten oturmasını
    sağlamak için, bu ödüle ulaşmak yaklaşık bir yıl sürer. Ödül dokuz seviyeden oluşup
    birinci seviye bir ayet için verilir. Dokuzuncu seviye ise Kutsal Kitap’ın tamamı için
    verilir.

# Description for a specific level
awards-master-award-level-n-description =
    En az { $verse_count ->
        [one] 1 ayet
       *[other] { $verse_count } ayet
    } çalışıldı.

# Specific description for level 9
awards-master-award-level-9-description =
    Kutsal Kitap’ın tamamını çalıştın!


## 'Sharer' award.

# Name
awards-sharer-award-name =
    Paylaşan

# General description
awards-sharer-award-general-description =
    Kamuya açık ayet dizinlerini oluşturunca verilen ödül.
    Beş seviyeden oluşup, bir ayet dizinine birinci seviye, 20 ayet dizinine ise beşinci
    seviye verilir.

# Description for a specific level
awards-sharer-award-level-n-description =
    { $count ->
        [one] Kamuya açık bir ayet dizini oluşturdu
       *[other] Kamuya açık { $count } ayet dizini oluşturdu
    }


## 'Trend Setter' award.

# Name
awards-trend-setter-award-name =
    Öncü

# General description
awards-trend-setter-award-level-general-description =
    Başkalar oluşturduğunuz ayet dizinleri kullanınca verilen ödül.
    En az beş kişinin oluşturduğunuz ayet dizinin kullanınca birinci seviye verilir.

# Description for a specific level
awards-trend-setter-award-level-n-description =
    Bu kullanıcı tarafından oluşturulan ayet dizinleri en az { $count } defa kullanıldı.


## 'Ace' award.

# Name
awards-ace-award-name =
    Birinci sınıf

# General description
awards-ace-award-general-description =
    Testte tam puan alınınca verilen ödül. Birinci seviye bir defa tam puan alınınca,
    verilir ikinci seviye arka arkaya iki defa tam puan alınca, üçüncü seviye arka arkaya
    dört defa tam pua, dördüncü seviye arka arakya sekiz defa tam puan alınca, vs.

# Description for first level
awards-ace-award-level-1-description =
    Testte tam puan aldı.

# Description for a specific level.
# $count is the number of times in a row they got 100%,
# will always be greater than 1.
awards-ace-award-level-n-description =
    Testte arka arkaya { $count } defa tam puan aldı


## 'Recruiter' award.

# Name
awards-recruiter-award-name =
    Tanık

# General description
# $url is a URL for the referral program help page.
awards-recruiter-award-general-description-html =
    Başkaları <a href="{ $url }">tanıtım programı</a> aracılığıyla üye olunca verilen ödül. Birinci seviye üye olan ilk kişi için verilir ve 20.000 puan değerindedir.

# Description for a specific level 'Recruiter' award.
# $url is a URL for the referral program help page.
# $count is the number of people recruited.
awards-recruiter-award-level-n-description-html =
    { $count ->
        [one] <a href="{ $url }">Tanıtım programı</a> aracılığıyla bir kişinin LearnScripture.net sitesine üye olmasını sağladı.
       *[other] Tanıtım programı</a> aracılığıyla { $count } kişinin LearnScripture.net sitesine üye olmasını sağladı.
    }


## 'Addict' award.

# Name
awards-addict-award-name =
    Tiryaki

# General description for 'Addict' award
awards-addict-award-general-description =
    Günün her saatinde test yapan kişilere verilen ödül.

# Description for 'Addict' award that appears on awardee's page
awards-addict-award-level-all-description =
    Günün her bir saatinde test yaptı.


## 'Organizer' award.

# Name
awards-organizer-award-name =
    Kurucu

# General description
awards-organizer-award-general-description =
    Başkalarını gruplara toplayan kişiye verilen ödül. İlk seviye için beş kişinin grubunuza katılması gerekir.

# Description for a specific level
awards-organizer-award-level-n-description =
    En az { $count } kişi tarafından kullanılan gruplar oluşturdu.

## 'Consistent learner' award.

# Name
awards-consistent-learner-award-name =
    İstikrarlı öğrenci

# General description
awards-consistent-learner-award-general-description =
    Belirli bir zaman içinde ara vermeden her gün yeni bir ayet ezberleyene verilen ödül. Ayetlerin sayılması için çalışılan ayetlerin yeni olması gerekir. Günler UTC zaman dilimine göre sayılır. Dokuz seviyeden oluşur. İlk seviye bir hafta için verilir, dokuzuncu ise iki yıl için.

# Specific description for level 1
awards-consistent-learner-award-level-1-description =
    Bir hafta boyunca her gün yeni bir ayet çalışıldı

awards-consistent-learner-award-level-2-description =
    İki hafta boyunca her gün yeni bir ayet çalışıldı

awards-consistent-learner-award-level-3-description =
    Bir ay boyunca her gün yeni bir ayet çalışıldı

awards-consistent-learner-award-level-4-description =
    Üç ay boyunca her gün yeni bir ayet çalışıldı

awards-consistent-learner-award-level-5-description =
    Altı ay boyunca her gün yeni bir ayet çalışıldı

awards-consistent-learner-award-level-6-description =
    Dokuz ay boyunca her gün yeni bir ayet çalışıldı

awards-consistent-learner-award-level-7-description =
    Bir yıl boyunca her gün yeni bir ayet çalışıldı

awards-consistent-learner-award-level-8-description =
    18 ay boyunca her gün yeni bir ayet çalışıldı

awards-consistent-learner-award-level-9-description =
    İki yıl boyunca her gün yeni bir ayet çalışıldı

# Title for award at a specific level.
# $name is award name,
# $level is a number indicating level.
awards-level-title =
    { $name } - { $level }. seviye

# Caption indicating a specific level award for a specific user
awards-level-awarded-for-user =
    { $username } { $award_level } seviyesinde { $award_name } ödülü aldı
