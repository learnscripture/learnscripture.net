from django.dispatch import Signal

new_account = Signal()
verse_started = Signal() # sender=Account
verse_tested = Signal() # sender=Identity, verse=UserVerseStatus
points_increase = Signal() # sender=Account, previous_points, points_added
scored_100_percent = Signal()
catechism_started = Signal() # sender=Account, catechism=TextVersion
